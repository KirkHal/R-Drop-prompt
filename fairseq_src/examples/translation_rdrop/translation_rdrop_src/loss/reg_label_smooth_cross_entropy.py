# Copyright (c) Facebook, Inc. and its affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import math
import torch
from fairseq import metrics, utils
from fairseq.criterions import FairseqCriterion, register_criterion


def label_smoothed_nll_loss_with_mask(lprobs, target, epsilon, mask, ignore_index=None, reduce=True):
    if target.dim() == lprobs.dim() - 1:
        target = target.unsqueeze(-1)
    nll_loss = -lprobs.gather(dim=-1, index=target)
    smooth_loss = -lprobs.sum(dim=-1, keepdim=True)
    if ignore_index is not None:
        # pad_mask = target.eq(ignore_index)
        pad_mask = mask
        # print("label_smoothed_nll_loss: mask:", pad_mask, pad_mask.shape)

        nll_loss.masked_fill_(pad_mask, 0.)
        smooth_loss.masked_fill_(pad_mask, 0.)
    else:
        nll_loss = nll_loss.squeeze(-1)
        smooth_loss = smooth_loss.squeeze(-1)
    if reduce:
        nll_loss = nll_loss.sum()
        smooth_loss = smooth_loss.sum()
    eps_i = epsilon / lprobs.size(-1)
    loss = (1. - epsilon) * nll_loss + eps_i * smooth_loss
    return loss, nll_loss

def label_smoothed_nll_loss(lprobs, target, epsilon, ignore_index=None, reduce=True):
    if target.dim() == lprobs.dim() - 1:
        target = target.unsqueeze(-1)
    nll_loss = -lprobs.gather(dim=-1, index=target)
    smooth_loss = -lprobs.sum(dim=-1, keepdim=True)
    if ignore_index is not None:
        pad_mask = target.eq(ignore_index)

        nll_loss.masked_fill_(pad_mask, 0.)
        smooth_loss.masked_fill_(pad_mask, 0.)
    else:
        nll_loss = nll_loss.squeeze(-1)
        smooth_loss = smooth_loss.squeeze(-1)
    if reduce:
        nll_loss = nll_loss.sum()
        smooth_loss = smooth_loss.sum()
    eps_i = epsilon / lprobs.size(-1)
    loss = (1. - epsilon) * nll_loss + eps_i * smooth_loss
    return loss, nll_loss

def vanilla_nll_loss(lprobs, target, epsilon, ignore_index=None, reduce=True):
    if target.dim() == lprobs.dim() - 1:
        target = target.unsqueeze(-1)
    nll_loss = -lprobs.gather(dim=-1, index=target)
    if ignore_index is not None:
        pad_mask = target.eq(ignore_index)
        nll_loss.masked_fill_(pad_mask, 0.)
    else:
        nll_loss = nll_loss.squeeze(-1)
    if reduce:
        nll_loss = nll_loss.sum()
    return nll_loss

@register_criterion('reg_label_smoothed_cross_entropy')
class RegLabelSmoothedCrossEntropyCriterion(FairseqCriterion):

    def __init__(self, task, sentence_avg, label_smoothing):
        super().__init__(task)
        self.sentence_avg = sentence_avg
        self.eps = label_smoothing

    @staticmethod
    def add_args(parser):
        """Add criterion-specific arguments to the parser."""
        # fmt: off
        parser.add_argument('--label-smoothing', default=0., type=float, metavar='D',
                            help='epsilon for label smoothing, 0 means no label smoothing')
        # fmt: on

    def compute_loss(self, model, net_output, sample, reduce=True):
        lprobs = model.get_normalized_probs(net_output, log_probs=True)
        lprobs = lprobs.view(-1, lprobs.size(-1))

        target = model.get_targets(sample, net_output).view(-1, 1)

        loss, nll_loss = label_smoothed_nll_loss(
            lprobs, target, self.eps, ignore_index=self.padding_idx, reduce=reduce,
        )
        return loss, nll_loss
    
    @staticmethod
    def reduce_metrics(logging_outputs) -> None:
        """Aggregate logging outputs from data parallel training."""
        loss_sum = sum(log.get('loss', 0) for log in logging_outputs)
        nll_loss_sum = sum(log.get('nll_loss', 0) for log in logging_outputs)
        ntokens = sum(log.get('ntokens', 0) for log in logging_outputs)
        sample_size = sum(log.get('sample_size', 0) for log in logging_outputs)

        metrics.log_scalar('loss', loss_sum / sample_size / math.log(2), sample_size, round=3)
        metrics.log_scalar('nll_loss', nll_loss_sum / ntokens / math.log(2), ntokens, round=3)
        metrics.log_derived('ppl', lambda meters: utils.get_perplexity(meters['nll_loss'].avg))

    @staticmethod
    def logging_outputs_can_be_summed() -> bool:
        """
        Whether the logging outputs returned by `forward` can be summed
        across workers prior to calling `reduce_metrics`. Setting this
        to True will improves distributed training speed.
        """
        return True

    def forward(self, model, sample, reduce=True):
        """Compute the loss for the given sample.

        Returns a tuple with three elements:
        1) the loss
        2) the sample size, which is used as the denominator for the gradient
        3) logging outputs to display while training
        """
        net_output = model(**sample['net_input'])
        loss, nll_loss = self.compute_loss(model, net_output, sample, reduce=reduce)
        sample_size = sample['target'].size(0) if self.sentence_avg else sample['ntokens']
        logging_output = {
            'loss': loss.data,
            'nll_loss': nll_loss.data,
            'ntokens': sample['ntokens'],
            'nsentences': sample['target'].size(0),
            'sample_size': sample_size,
        }
        return loss, sample_size, logging_output
    
    def compute_kl_loss(self, model, net_output, pad_mask=None, reduce=True):
        net_prob = model.get_normalized_probs(net_output, log_probs=True)
        net_prob_tec = model.get_normalized_probs(net_output, log_probs=False)

        p, q = torch.split(net_prob, net_prob.size(0)//2, dim=0)
        p_tec, q_tec = torch.split(net_prob_tec, net_prob_tec.size(0)//2, dim=0)
        
        p_loss = torch.nn.functional.kl_div(p, q_tec, reduction='none')
        q_loss = torch.nn.functional.kl_div(q, p_tec, reduction='none')
        
        if pad_mask is not None:
            p_loss.masked_fill_(pad_mask, 0.)
            q_loss.masked_fill_(pad_mask, 0.)

        if reduce:
            p_loss = p_loss.sum()
            q_loss = q_loss.sum()

        loss = (p_loss + q_loss) / 2
        return loss

    def mask_creator(self, tgt, mask):
        pad_list = []
        for sent in tgt:
            pad_num = 0
            for token in sent:
                if int(token.item()) != 19:
                    pad_num += 1
                else:
                    break
            pad_list.append(pad_num)
            if len(pad_list) == tgt.shape[0]/2:
                break

        mask_output = mask.clone()
        for index, mask_sent in enumerate(mask_output):
            for i, mask_item in enumerate(mask_sent):
                if not mask_item:
                    if i >= pad_list[index]:
                        mask_sent[i] = bool(True)
        return mask_output

    def pos_mask_creator(self, tgt, mask):
        pad_list = []
        for sent in tgt:
            pad_num = 0
            for token in sent:
                if int(token.item()) != 19:
                    pad_num += 1
                else:
                    break
            pad_list.append(pad_num)
            if len(pad_list) == tgt.shape[0]/2:
                break

        mask_output = mask.clone()
        for index, mask_sent in enumerate(mask_output):
            for i, mask_item in enumerate(mask_sent):
                if not mask_item:
                    if i < pad_list[index]:
                        mask_sent[i] = bool(True)
        return mask_output

    def mask_process(self, tgt, mask):
        mask_shape = int(tgt.numel()/2)

        mask_processed = mask.clone()
        mask_processed = mask_processed.squeeze().reshape(mask_shape, 1)
        mask_processed = torch.cat((mask_processed, mask_processed.clone()), dim=0)
        return mask_processed

    def forward_reg(self, model, sample, optimizer, reg_alpha, ignore_grad, reduce=True):
        
        sample_input = sample['net_input']
        sample_concat_input = {
            'src_tokens': torch.cat([sample_input['src_tokens'], sample_input['src_tokens'].clone()], 0),
            'src_lengths': torch.cat([sample_input['src_lengths'], sample_input['src_lengths'].clone()], 0),
            'prev_output_tokens': torch.cat([sample_input['prev_output_tokens'], sample_input['prev_output_tokens'].clone()], 0),
        }

        # print("criterion: forward_reg: sample_input:", sample_input)
        # print("criterion: forward_reg: sample_concat_input:")
        # print("sample_concat_input['src_tokens']:", sample_concat_input['src_tokens'], sample_concat_input['src_tokens'].shape)
        # print("sample_concat_input['src_lengths']:", sample_concat_input['src_lengths'], sample_concat_input['src_lengths'].shape)
        # print("sample_concat_input['prev_output_tokens']:", sample_concat_input['prev_output_tokens'], sample_concat_input['prev_output_tokens'].shape)
        
        net_output = model(**sample_concat_input)
        # print("criterion: forward_reg: net_output:", net_output)

        lprobs = model.get_normalized_probs(net_output, log_probs=True)
        lprobs = lprobs.view(-1, lprobs.size(-1))
        # print("criterion: forward_reg: lprobs:", lprobs, lprobs.shape)

        target = model.get_targets(sample, net_output)

        pad_mask = target.unsqueeze(-1).eq(self.padding_idx)
        # print("criterion: forward_reg: pad_mask:", pad_mask, pad_mask.shape)
        # print("criterion: forward_reg: padding_idx:", self.padding_idx)

        target = torch.cat([target, target.clone()], dim=0)
        # print("criterion: forward_reg: target:", target, target.shape)

        pos_mask = self.pos_mask_creator(target, pad_mask)
        # print("criterion: forward_reg: pos_mask:", pos_mask, pos_mask.shape)

        pad_mask = self.mask_creator(target, pad_mask)
        # print("criterion: forward_reg: pad_mask:", pad_mask, pad_mask.shape)

        pad_mask_processed = self.mask_process(target, pad_mask)
        # print("criterion: forward_reg: pad_mask_processed:", pad_mask_processed, pad_mask_processed.shape)
        pos_mask_processed = self.mask_process(target, pos_mask)
        # print("criterion: forward_reg: pos_mask_processed:", pos_mask_processed, pos_mask_processed.shape)

        loss, nll_loss = label_smoothed_nll_loss_with_mask(
            lprobs, target.view(-1, 1), self.eps, pad_mask_processed, ignore_index=self.padding_idx, reduce=reduce,
        )
        loss_pos, nll_loss_pos = label_smoothed_nll_loss_with_mask(
            lprobs, target.view(-1, 1), self.eps, pos_mask_processed, ignore_index=self.padding_idx, reduce=reduce,
        )
        # print("nll_loss:", nll_loss.item())
        # print("nll_loss_pos:", nll_loss_pos.item())

        kl_loss = self.compute_kl_loss(model, net_output, pad_mask)
        kl_loss_pos = self.compute_kl_loss(model, net_output, pos_mask)
        # print("kl_loss:", kl_loss.item())
        # print("kl_loss_pos:", kl_loss_pos.item())

        loss += reg_alpha * kl_loss
        loss_pos += reg_alpha * kl_loss_pos
        # print("loss:", loss.item(), "loss_pos:", loss_pos.item())

        loss_ratio = 0.5
        loss += loss_pos * loss_ratio
        # print("total_loss:", loss.item())

        if ignore_grad:
            loss *= 0
        with torch.autograd.profiler.record_function("backward"):
            optimizer.backward(loss)

        ntokens = sample['ntokens']
        nsentences = sample['target'].size(0)
        sample_size = sample['ntokens']
        logging_output = {
            'loss': utils.item(loss.data) if reduce else loss.data,
            'nll_loss': utils.item(nll_loss.data) if reduce else nll_loss.data,
            'ntokens': ntokens,
            'nsentences': nsentences,
            'sample_size': sample_size,
        }
        # print("criterion: forward_reg: logging_output:", logging_output)

        return loss, sample_size, logging_output

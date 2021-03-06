import torch

#TODO： torch to numpy

def get_preds(scores):
    ''' get predictions from score maps in torch Tensor
        return type: torch.LongTensor
    '''
    assert scores.dim() == 4, 'Score maps should be 4-dim'
    maxval, idx = torch.max(scores.view(scores.size(0), scores.size(1), -1), 2)

    maxval = maxval.view(scores.size(0), scores.size(1), 1)
    idx = idx.view(scores.size(0), scores.size(1), 1)

    preds = idx.repeat(1, 1, 2).float()

    preds[:, :, 0] = preds[:, :, 0] % scores.size(3)
    preds[:, :, 1] = torch.floor(preds[:, :, 1] / scores.size(3)) + 1

    pred_mask = maxval.gt(0).repeat(1, 1, 2).float()
    preds *= pred_mask
    return preds

def calc_dists(preds, target, normalize):
    preds = preds.float()
    target = target.float()
    dists = torch.zeros(preds.size(1), preds.size(0))
    for n in range(preds.size(0)):
        for c in range(preds.size(1)):
            if target[n, c, 0] > 0 and target[n, c, 1] > 0:
                dists[c, n] = torch.dist(preds[n, c, :], target[n, c, :])/normalize[n]
            else:
                dists[c, n] = -1
    return dists

def dist_acc(dists, thr=0.5):
    ''' Return percentage below threshold while ignoring values with a -1 '''
    if dists.ne(-1).sum() > 0:
        return dists.le(thr).eq(dists.ne(-1)).sum()*1.0 / dists.ne(-1).sum()
    else:
        return -1

def accuracy(output, target, idxs, thr=0.5):
    ''' Calculate accuracy according to PCK, but uses ground truth heatmap rather than x,y locations
        First value to be returned is average accuracy across 'idxs', followed by individual accuracies
    '''
    preds = get_preds(output)
    gts = get_preds(target)
    norm = torch.ones(preds.size(0))*output.size(3)/10
    dists = calc_dists(preds, gts, norm)

    acc = torch.zeros(len(idxs)+1)
    avg_acc = 0
    cnt = 0

    for i in range(len(idxs)):
        acc[i+1] = dist_acc(dists[idxs[i]])
        if acc[i+1] >= 0:
            avg_acc = avg_acc + acc[i+1]
            cnt += 1

    if cnt != 0:
        acc[0] = avg_acc / cnt
    return acc

# def heatmapAccuracy(output, target, th, idxs):
#     '''Calculate accuracy according to PCK, but uses ground truth heatmap rather than x,y locations
#     First value to be returned is average accuracy across 'idxs', followed by individual accuracies
#     '''


if __name__ == '__main__':
    import warnings
    warnings.filterwarnings("ignore")
    from datasets.lsp import LSPMPIIData
    dataset = LSPMPIIData('../data', split='train', meta=True)
    image, label, _, meta = dataset[0]
    print(accuracy(torch.Tensor(label).unsqueeze(0), torch.Tensor(label).unsqueeze(0), dataset.accIdxs))
    print(meta)

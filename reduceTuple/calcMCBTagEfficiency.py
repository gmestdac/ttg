#! /usr/bin/env python
import ROOT, pickle, os
ROOT.gROOT.SetBatch(True)

import argparse
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel', action='store',      default='INFO', nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'], help="Log level for logging")
argParser.add_argument('--sample',   action='store',      default='TTJets_pow')
args = argParser.parse_args()

from ttg.tools.logger import getLogger
log = getLogger(args.logLevel)

from ttg.reduceTuple.btagEfficiency import getPtBins, getEtaBins
from ttg.reduceTuple.objectSelection import setIDSelection, selectLeptons, selectPhotons, goodJets
from ttg.samples.Sample import createSampleList, getSampleFromList
sampleList           = createSampleList(os.path.expandvars('$CMSSW_BASE/src/ttg/samples/data/tuples.conf'))
sample               = getSampleFromList(sampleList, args.sample)
chain                = sample.initTree()
setIDSelection(chain, 'eleSusyLoose-phoCB')

def getBTagMCTruthEfficiencies(c, btagWP):  # pylint: disable=R0912
  passing = {}
  total   = {}
  for ptBin in getPtBins():
    for etaBin in getEtaBins():
      for f in ['b', 'c', 'other']:
        name = str(ptBin) + str(etaBin) + f
        passing[name] = 0.
        total[name]   = 0.

  for i in sample.eventLoop():
    c.GetEntry(i)
    if not selectLeptons(c, c, 2):       continue
    if not selectPhotons(c, c, 2, True): continue
    goodJets(c, c)
 
    for j in c.jets:
      pt     = c._jetPt[j]
      eta    = abs(c._jetEta[j])
      flavor = abs(c._jetHadronFlavor[j])
      for ptBin in getPtBins():
        if pt >= ptBin[0] and (pt < ptBin[1] or ptBin[1] < 0):
          for etaBin in getEtaBins():
            if abs(eta) >= etaBin[0] and abs(eta) < etaBin[1]:
              if abs(flavor) == 5:   f = 'b' 
              elif abs(flavor) == 4: f = 'c'
              else:                 f = 'other'
              name = str(ptBin) + str(etaBin) + f
              if c._jetDeepCsv_b[j] + c._jetDeepCsv_bb[j] > btagWP: passing[name] += c._weight
              total[name] += c._weight

  mceff = {}
  for ptBin in getPtBins():
    mceff[tuple(ptBin)] = {}
    for etaBin in getEtaBins():
      mceff[tuple(ptBin)][tuple(etaBin)] = {}
      for f in ['b', 'c', 'other']:
        name = str(ptBin) + str(etaBin) + f
        mceff[tuple(ptBin)][tuple(etaBin)][f] = passing[name]/total[name] if total[name] > 0 else 0
 
  return mceff

res = getBTagMCTruthEfficiencies(chain, btagWP=0.6324)

pickle.dump(res, file(os.path.expandvars('$CMSSW_BASE/src/ttg/reduceTuple/data/btagEfficiencyData/deepCSV_' + args.sample + '.pkl'), 'w'))
log.info('Efficiencies deepCSV:')
log.info(res)
log.info('Finished')

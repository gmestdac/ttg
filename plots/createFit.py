#! /usr/bin/env python
import argparse
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel',       action='store',      default='INFO',      nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'], help="Log level for logging")
argParser.add_argument('--checkStability', action='store_true', default=False)
args = argParser.parse_args()

from ttg.plots.plot         import Plot, getHistFromPkl
from ttg.tools.logger       import getLogger
from ttg.plots.combineTools import handleCombine
log = getLogger(args.logLevel)

import os, ROOT, shutil
ROOT.gROOT.SetBatch(True)


def writeStatVariation(hist, prefix):
  for i in range(hist.GetNbinsX()):
    bin  = i+1
    up   = hist.Clone()
    down = hist.Clone()
    up.SetBinContent(  bin, hist.GetBinContent(bin)+hist.GetBinError(bin))
    down.SetBinContent(bin, hist.GetBinContent(bin)-hist.GetBinError(bin))
    up.Write(prefix + str(i) + 'Up')
    down.Write(prefix + str(i) + 'Down')

for channel in ['ee', 'emu', 'mumu']:
  mcPurities = []
  for pseudoData in [True, False]:
    for j in (range(-5, 20, 1) if pseudoData and args.checkStability else [0]):
      log.info('Creating templates and card for ' + channel)
      dataCard = 'purityFit_' + channel + ('_pseudoData' if pseudoData else '')
      selection = 'llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet2p-deepbtag1p'
      randomConeSelection    = getHistFromPkl(('eleSusyLoose-phoCBnoChgIso', channel, selection), 'photon_randomConeIso', ['data'])
      sigmaIetaIetaSideBand  = getHistFromPkl(('sigmaIetaIetaMatchMC',       channel, selection), 'photon_chargedIso',    ['data'])
      if pseudoData:
        chargedIsoTTGamma    = getHistFromPkl(('eleSusyLoose-phoCBnoChgIso', channel, selection), 'photon_chargedIso',    ['t#bar{t}#gamma'])
        chargedIsoOther      = getHistFromPkl(('eleSusyLoose-phoCBnoChgIso', channel, selection), 'photon_chargedIso',    ['TTJets'])
        chargedIsoOther.Add(   getHistFromPkl(('eleSusyLoose-phoCBnoChgIso', channel, selection), 'photon_chargedIso',    ['Z#gamma']))
        chargedIsoOther.Add(   getHistFromPkl(('eleSusyLoose-phoCBnoChgIso', channel, selection), 'photon_chargedIso',    ['Drell-Yan']))
        chargedIsoOther.Add(   getHistFromPkl(('eleSusyLoose-phoCBnoChgIso', channel, selection), 'photon_chargedIso',    ['single-t']))
        chargedIsoOther.Add(   getHistFromPkl(('eleSusyLoose-phoCBnoChgIso', channel, selection), 'photon_chargedIso',    ['multiboson']))
        chargedIsoOther.Add(   getHistFromPkl(('eleSusyLoose-phoCBnoChgIso', channel, selection), 'photon_chargedIso',    ['t#bar{t}+V']))
        chargedIsoTTGamma.Scale(1+j*0.1)
        chargedIsoData = chargedIsoTTGamma.Clone()
        chargedIsoData.Add(chargedIsoOther)
        mcResult = chargedIsoTTGamma.Integral()/chargedIsoData.Integral()
        log.info('Expected fit for mc: %.3f' % mcResult)
      else:
        chargedIsoData      = getHistFromPkl(('eleSusyLoose-phoCBnoChgIso',  channel, selection), 'photon_chargedIso',    ['data'])
      randomConeSelection.Scale(chargedIsoData.Integral()/randomConeSelection.Integral())
      sigmaIetaIetaSideBand.Scale(chargedIsoData.Integral()/sigmaIetaIetaSideBand.Integral())

      rootfile = ROOT.TFile(dataCard + '.root', 'RECREATE')
      randomConeSelection.Write('signal')
      sigmaIetaIetaSideBand.Write('background')
      writeStatVariation(randomConeSelection,   'signal_statSig')
      writeStatVariation(sigmaIetaIetaSideBand, 'background_statBack')
      chargedIsoData.Write('data_obs')

      with open('combineCard.txt', 'r') as source:
        with open(dataCard + '.txt', 'w') as destination:
          for line in source:
            line = line.replace('$FILE',        dataCard + '.root')
            destination.write(line)
          for i in range(chargedIsoData.GetNbinsX()):
            continue # adding statistics does not work
            if randomConeSelection.GetBinContent(i+1):   destination.write('statSig' + str(i) + '  shapeN2      1          -\n')
            if sigmaIetaIetaSideBand.GetBinContent(i+1): destination.write('statBack' + str(i) + ' shapeN2      -          1\n')
      rootfile.Close()

      result = handleCombine(dataCard)

      import ttg.tools.style as styles
      chargedIsoData.style        = styles.errorStyle(ROOT.kBlack)
      randomConeSelection.style   = styles.fillStyle(ROOT.kRed)
      sigmaIetaIetaSideBand.style = styles.fillStyle(ROOT.kBlue)

      randomConeSelection2   = randomConeSelection.Clone()
      sigmaIetaIetaSideBand2 = sigmaIetaIetaSideBand.Clone()
      randomConeSelection2.style   = styles.fillStyle(ROOT.kRed)
      sigmaIetaIetaSideBand2.style = styles.fillStyle(ROOT.kBlue)
      randomConeSelection2.Scale(result[0])
      sigmaIetaIetaSideBand2.Scale(1-result[0])

      chargedIsoData.texName = 'data'
      randomConeSelection.texName = 'signal (prefit)'
      sigmaIetaIetaSideBand.texName = 'background (prefit)'
      randomConeSelection2.texName = 'signal (after fit)'
      sigmaIetaIetaSideBand2.texName = 'background (after fit)'


      prefit        = Plot('prefit', 'chargedIso(#gamma) (GeV)', None, None, overflowBin=None, stack=[[]], texY='Events')
      prefit.stack  = [[randomConeSelection,sigmaIetaIetaSideBand],[chargedIsoData]]
      prefit.histos = {i:i for i in sum(prefit.stack, [])}

      fit        = Plot('fit', 'chargedIso(#gamma) (GeV)', None, None, overflowBin=None, stack=[[]], texY='Events')
      fit.stack  = [[randomConeSelection2,sigmaIetaIetaSideBand2],[chargedIsoData]]
      fit.histos = {i:i for i in sum(fit.stack, [])}

      if j==0:
        from ttg.tools.style import drawLumi
        for plot in [fit, prefit]:
          plot.draw(plot_directory = './fitPlots/' + channel + ('_pseudoData' if pseudoData else ''),
                   ratio   = {'yRange':(0.1,1.9),'texY': 'ratio'},
                   logX    = False, logY = False, sorting = False,
                   yRange  = (0.0001, "auto"),
                   drawObjects = drawLumi(None, 35.9),
          )

      if pseudoData:
        mcPurities.append((mcResult, result))


      def purity(bin, sig, back):
        return randomConeSelection2.Integral(0, bin)*sig/(randomConeSelection2.Integral(0, bin)*sig+sigmaIetaIetaSideBand2.Integral(0, bin)*back)

      purity5GeV = purity(5, 1, 1)
      purity1GeV = purity(1, 1, 1)

      signalUp       = (result[0]+result[1])/result[0]
      backgroundUp   = (1-(result[0]+result[1]))/(1-result[0])
      signalDown     = (result[0]+result[2])/result[0]
      backgroundDown = (1-(result[0]+result[2]))/(1-result[0])

      purity5GeVUp   = purity(5, signalUp,   backgroundUp)
      purity5GeVDown = purity(5, signalDown, backgroundDown)
      purity1GeVUp   = purity(1, signalUp,   backgroundUp)
      purity1GeVDown = purity(1, signalDown, backgroundDown)

      log.info('Result purity 5GeV: %.2f %.2f/+%.2f' % (purity5GeV, purity5GeVDown-purity5GeV, purity5GeV-purity5GeVUp))
      log.info('Result purity 1GeV: %.2f %.2f/+%.2f' % (purity1GeV, purity1GeVDown-purity1GeV, purity1GeV-purity1GeVUp))

  if args.checkStability:
    c     = ROOT.TCanvas(channel, channel)
    graph = ROOT.TGraphAsymmErrors()
    graph.SetTitle(';MC truth photon purity;Fit result photon purity')
    for i, (mcPurity, fitPurity) in enumerate(mcPurities):
      graph.SetPoint(i, mcPurity, fitPurity[0])
      graph.SetPointError(i, 0, 0, -fitPurity[1], fitPurity[2])
    graph.GetXaxis().SetLimits(0.31,0.9)
    graph.SetMinimum(0.31)
    graph.SetMaximum(0.9)
    graph.Draw("AP0")
    line = ROOT.TLine(0.31,0.31,0.9,0.9);
    line.Draw()
    c.Print('./fitPlots/' + channel + '/purityComparison.pdf')
    c.Print('./fitPlots/' + channel + '/purityComparison.png')
log.info('Finished')

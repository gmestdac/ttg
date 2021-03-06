from ttg.tools.logger import getLogger
log = getLogger()
import ROOT, os
from ttg.plots.systematics import linearSystematics

#
# A few mappings when the combine nuisance name does not exactly match with the name of the samples in the plots
#
def mapName(name):
  if name == 'r':            return 'TTGamma_norm'
  if name.count('hadronic'): return 'hadronic photons_norm'
  if name.count('fake'):     return 'hadronic fakes_norm'
  else:                      return name


#
# Update the pulls and constraints (saved in global variable assuming it won't change)
#
pullsAndConstraints = {}
dataCard = None
def updatePullsAndConstraints(newDataCard = 'srFit'):
  global dataCard  # pylint: disable=W0603
  if not dataCard or dataCard != newDataCard:
    dataCard    = newDataCard
    filename    = os.path.expandvars('$CMSSW_BASE/src/ttg/plots/combine/' + dataCard + '_fitDiagnostics.root')
    resultsFile = ROOT.TFile(filename)
    fitResults  = resultsFile.Get("fit_s").floatParsFinal()
    for r in [fitResults.at(i) for i in range(fitResults.getSize())]:
      pullsAndConstraints[mapName(r.GetName())] = (r.getVal(), r.getAsymErrorHi())
    log.info('Loaded pulls and constrains from ' + filename)

#
# To avoid too much repeated logging
#
alreadyShownDebug = []
def showLogDebugOnce(logMsg):
  if logMsg not in alreadyShownDebug:
    log.info(logMsg)
    alreadyShownDebug.append(logMsg)

alreadyShownWarning = []
def showLogWarningOnce(logMsg):
  if logMsg not in alreadyShownWarning:
    log.warning(logMsg)
    alreadyShownWarning.append(logMsg)

#
# Applying post-fit values, given a dictionary of sample --> histogram or pkl-histname --> histogram
#
def applyPostFitScaling(histos, postFitInfo, sysHistos=None):  # pylint: disable=R0912
  updatePullsAndConstraints(postFitInfo)
  postHistos = {s : h.Clone() for s, h in histos.iteritems()}                                                    # Create clones (such that we still can access the prefit values below)
  if sysHistos:                                                                                                  # First add pulls of the nuisances to each sample (real post-fit plots are impossible,
    for sample, h in postHistos.iteritems():                                                                     # but this is as close as it gets)
      name = sample if isinstance(sample, str) else (sample.name + sample.texName)
      if name.count('data'): continue                                                                            # Skip data
      for i in pullsAndConstraints:
        if any(x in i for x in ['norm', 'prop', 'nonPrompt']): continue                                          # Skip warning for these cases
        try:
          value = pullsAndConstraints[i][0]
          if i in linearSystematics and False:
            h.Scale(1+value*linearSystematics[i][1]/100.)
          else:
            if value > 0: nuisanceHist = sysHistos[i + 'Up'][name]
            else:         nuisanceHist = sysHistos[i + 'Down'][name]
            for j in range(h.GetNbinsX()+2):
              var = nuisanceHist.GetBinContent(j)
              nom = histos[sample].GetBinContent(j)
              h.SetBinContent(j, h.GetBinContent(j) + abs(var-nom)*value)
          showLogDebugOnce('Applying pull for nuisance ' + i + ' with ' + str(value) + ' to ' + name)
        except:
          showLogWarningOnce('Cannot apply pull for nuisance ' + i + ' to ' + name)
  for i in pullsAndConstraints:
    if 'norm' in i:                                                                                              # Then scale each MC given the pull on the rate parameter
      foundSampleToScale = False
      for sample, h in postHistos.iteritems():
        name = sample if isinstance(sample, str) else (sample.name + sample.texName)
        if name.count(i.split('_')[0]):
          value = pullsAndConstraints[i][0]
          h.Scale(value)
          showLogDebugOnce('Applying post-fit scaling value of ' + str(value) + ' to ' + name)
          foundSampleToScale = True
      if not foundSampleToScale:
        showLogWarningOnce('Could not find where to apply post-fit scaling for ' + i)

  return postHistos

#
# Calculate resulting uncertainty
#
def applyPostFitConstraint(sys, uncertainty, postFitInfo):
  updatePullsAndConstraints(postFitInfo)
  for i in pullsAndConstraints:
    if i in sys:
      showLogDebugOnce('Applying constraint ' + str(pullsAndConstraints[i][1]) + ' on ' + sys + ' (taking constraint from ' + i + ')')
      return uncertainty*pullsAndConstraints[i][1]
  else:
    if not 'Stat' in sys and postFitInfo.count('srFit'): showLogWarningOnce('Could not find constrain for ' + sys)
    return uncertainty

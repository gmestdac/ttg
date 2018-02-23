#
# Photon categorization functions
#
from ttg.tools.helpers import deltaR

def isSignalPhoton(tree, index, oldDefinition=False):
  if not oldDefinition:
    return tree._phTTGMatchCategory[index]==1
  else:
    mcIndex = tree._phMatchMCPhotonAN15165[index]
    if mcIndex < 0:                                                                                               return False
    if (tree._gen_phPt[mcIndex] - tree._phPt[index])/tree._gen_phPt[mcIndex] > 0.1:                               return False
    if (tree._gen_phEta[mcIndex] - tree._phEta[index])/tree._gen_phEta[mcIndex] > 0.005:                          return False
    if deltaR(tree._gen_phEta[mcIndex], tree._phEta[index], tree._gen_phPhi[mcIndex], tree._phPhi[index]) > 0.01: return False
    if not tree._gen_phPassParentage[mcIndex]:                                                                    return False
    if tree._gen_phMinDeltaR[mcIndex] < 0.2:                                                                      return False
    return True

def isHadronicPhoton(tree, index, oldDefinition=False):
  if not oldDefinition:
    return tree._phTTGMatchCategory[index]==3
  else:
    mcIndex = tree._phMatchMCPhotonAN15165[index]
    if mcIndex < -1:                return False
    if isSignalPhoton(tree, index): return False
    return True

def isGoodElectron(tree, index, oldDefinition=False):
  if not oldDefinition:
    return tree._phTTGMatchCategory[index]==2
  else:
    if isSignalPhoton(tree, index):   return False
    if isHadronicPhoton(tree, index): return False
    mcIndex = tree._phMatchMCLeptonAN15165[index]
    if mcIndex < 0:                                                                                             return False
    if (tree._gen_lPt[mcIndex] - tree._phPt[index])/tree._gen_lPt[mcIndex] > 0.1:                               return False
    if not tree._gen_lPassParentage[mcIndex]:                                                                   return False
    if tree._gen_lMinDeltaR[mcIndex] < 0.2:                                                                     return False
    if deltaR(tree._gen_lEta[mcIndex], tree._phEta[index], tree._gen_lPhi[mcIndex], tree._phPhi[index]) > 0.04: return False
    if (tree._gen_lEta[mcIndex] - tree._phEta[index])/tree._gen_lEta[mcIndex] > 0.005:                          return False
    return True;

def isHadronicFake(tree, index, oldDefinition=False):
  if not oldDefinition:
    return tree._phTTGMatchCategory[index]==4
  else:
    if isSignalPhoton(tree, index):   return False
    if isHadronicPhoton(tree, index): return False
    if isGoodElectron(tree, index):   return False
    return True

def photonCategoryNumber(tree, index, oldDefinition=False):
  if not oldDefinition:                              return tree._phTTGMatchCategory[index]
  if isSignalPhoton(tree, index, oldDefinition):     return 1
  elif isGoodElectron(tree, index, oldDefinition):   return 2
  elif isHadronicPhoton(tree, index, oldDefinition): return 3
  else:                                              return 4

def checkMatch(tree, index, oldDefinition=False):
  if not tree.checkMatch:                                                  return True
  if tree.genuine        and isSignalPhoton(tree, index, oldDefinition):   return True
  if tree.hadronicPhoton and isHadronicPhoton(tree, index, oldDefinition): return True
  if tree.misIdEle       and isGoodElectron(tree, index, oldDefinition):   return True
  if tree.hadronicFake   and isHadronicFake(tree, index, oldDefinition):   return True
  return False

def checkPrompt(tree, index):
  if tree.nonprompt and tree._phIsPrompt[index]:     return False
  if tree.prompt    and not tree._phIsPrompt[index]: return False
  return True

def checkSigmaIetaIeta(tree, index):
  cut = (0.01022 if abs(tree._phEta[index]) < 1.566 else  0.03001)                        # forward region needs much higher cut
  if   tree.passSigmaIetaIeta and tree._phSigmaIetaIeta[index] > cut:                     return False
  elif tree.failSigmaIetaIeta and tree._phSigmaIetaIeta[index] < cut:                     return False
  if tree._phSigmaIetaIeta[index] > (0.016 if abs(tree._phEta[index]) < 1.566 else 0.04): return False
  return True

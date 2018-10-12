import ROOT, socket, os, shutil, subprocess
from math import pi, sqrt

#
# Get some fixed paths
#
userGroup       = os.path.expandvars('$USER')[0:1]
plotDir         = os.path.expandvars(('/eos/user/' + userGroup + '/$USER/www/ttG/')       if 'lxp' in socket.gethostname() else '/user/$USER/www/ttG/')
reducedTupleDir = os.path.expandvars(('/eos/user/' + userGroup + '/$USER/reducedTuples/') if 'lxp' in socket.gethostname() else '/user/$USER/public/reducedTuples/') 

#
# Check if valid ROOT file exists
#
def isValidRootFile(fname):
  f = ROOT.TFile(fname)
  if not f: return False
  try:
    return not (f.IsZombie() or f.TestBit(ROOT.TFile.kRecovered) or f.GetListOfKeys().IsEmpty())
  finally:
    f.Close()

#
# Get object (e.g. hist) from file using key, and keep in memory after closing
#
def getObjFromFile(fname, hname):
  assert isValidRootFile(fname)
  try:
    f = ROOT.TFile(fname)
    f.cd()
    htmp = f.Get(hname)
    if not htmp: return None
    ROOT.gDirectory.cd('PyROOT:/')
    res = htmp.Clone()
    return res
  finally:
    f.Close()

#
# Copy the index.php file to plotting directory and all mother directories within the plotDir
#
def copyIndexPHP(directory):
  if not os.path.exists(directory): os.makedirs(directory)
  subdirs = directory.split('/')
  for i in range(1,len(subdirs)):
    p = '/'.join(subdirs[:-i])
    if not plotDir in p: continue
    index_php = os.path.join(p, 'index.php')
    if os.path.exists(index_php): continue
    shutil.copyfile(os.path.expandvars('$CMSSW_BASE/src/ttg/tools/php/index.php'), index_php)

#
# Update the latest git information
#
def updateGitInfo():
  os.system('(git log -n 1;git diff) &> git.txt')

#
# Copy git info for plot
#
def copyGitInfo(path):
  if os.path.isfile('git.txt'):
    shutil.copyfile('git.txt', path)


#
# Edit the info file in a given path
#
def editInfo(path):
  editor = os.getenv('EDITOR', 'vi')
  subprocess.call('%s %s' % (editor, os.path.join(path, 'info.txt')), shell=True)


#
# Delta phi and R function
#
def deltaPhi(phi1, phi2):
  dphi = phi2-phi1
  if dphi > pi:   dphi -= 2.0*pi
  if dphi <= -pi: dphi += 2.0*pi
  return abs(dphi)

def deltaR(eta1, eta2, phi1, phi2):
  return sqrt(deltaPhi(phi1, phi2)**2 + (eta1-eta2)**2)

#
# Safe hist add
#
def addHist(first, second):
  if first and second: first.Add(second)
  elif second:         first = second.Clone()
  return first

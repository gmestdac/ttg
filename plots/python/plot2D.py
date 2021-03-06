from ttg.tools.logger import getLogger
log = getLogger()

import ROOT, os, numpy
from ttg.tools.helpers import copyIndexPHP, copyGitInfo
from ttg.plots.plot import Plot

#
# Plot class for 2D
# Disable warnings about different number of arguments for overriden method 
# pylint: disable=W0221
#
class Plot2D(Plot):
  defaultStack = None

  @staticmethod
  def setDefaults(stack = None):
    Plot2D.defaultStack = stack

  def __init__(self, name, texX, varX, binningX, texY, varY, binningY, stack=None):  # pylint: disable=R0913
    Plot.__init__(self, name, texX, varX, binningX, stack=(stack if stack else Plot2D.defaultStack), texY=texY, overflowBin=False, normBinWidth=False)
    self.varY        = varY
    self.binningX    = self.binning

    if type(binningY)==type([]):   self.binningY = (len(binningY)-1, numpy.array(binningY))
    elif type(binningY)==type(()): self.binningY = binningY

    self.histos = {}
    for s in sum(self.stack, []):
      name           = self.name + s.name
      self.histos[s] = ROOT.TH2F(name, name, *(self.binningX+self.binningY))


  def fill(self, sample, weight=1.):
    self.histos[sample].Fill(self.varX(sample.chain), self.varY(sample.chain), weight)


  #
  # Stacking the hist, called during the draw function
  #
  def stackHists(self, histsToStack, sorting=True):
    if sorting: histsToStack.sort(key=lambda h  : -h.Integral())

    # Add up stacks
    for i, _ in enumerate(histsToStack):
      for j in range(i+1, len(histsToStack)):
        histsToStack[i].Add(histsToStack[j])

    return histsToStack[:1] # do not show sub-contributions in 2D

  def getYields(self, binX=None, binY=None):
    if binX and binY: return {s.name : h.GetBinContent(binX, binY) for s, h in self.histos.iteritems()}
    else:             return {s.name : h.Integral()                for s, h in self.histos.iteritems()}


  #
  # Draw function, might need some refactoring
  # pylint: disable=R0913,R0914,R0915
  #
  def draw(self, \
          zRange = None,
          extensions = None, 
          plot_directory = ".", 
          logX = False, logY = False, logZ = True, 
          drawObjects = None,
          drawOption = 'COLZ',
          widths = None,
          ):
    ''' plot: a Plot2D instance
        zRange: None ( = ROOT default) or [low, high] 
        extensions: ["pdf", "png", "root"] (default)
        logX: True/False (default), logY: True/False(default), logZ: True/False(default)
        drawObjects = [] Additional ROOT objects that are called by .Draw() 
        widths = {} (default) to update the widths. Values are {'y_width':500, 'x_width':500, 'y_ratio_width':200}
    '''

    import ttg.tools.style as style
    style.setDefault2D(drawOption=='COLZ')

    # default_widths    
    default_widths = {'y_width':500, 'x_width':500, 'y_ratio_width':200}
    if widths: default_widths.update(widths)

    histDict = {i: h.Clone() for i, h in self.histos.iteritems()}

    # Apply style to histograms and add overflow bin
    for s, h in histDict.iteritems():
      if hasattr(s, 'style2D'): s.style2D(h)
      h.texName = s.texName

    # Transform histDict --> histos where the stacks are added up
    # Note self.stack is of form [[A1, A2, A3,...],[B1,B2,...],...] where the sublists need to be stacked
    histos = []
    for stack in self.stack:
      histsToStack = [histDict[s] for s in stack]
      histos.append(self.stackHists(histsToStack))

    # delete canvas if it exists
    if hasattr("ROOT","c1"): del ROOT.c1 
    c1 = ROOT.TCanvas("ROOT.c1", "drawHistos", 200, 10, default_widths['x_width'], default_widths['y_width'])

    c1.SetLogx(logX)
    c1.SetLogy(logY)
    c1.SetLogz(logZ)

    same = ""
    for histo in (sum(histos, []) if drawOption.count('SCAT') else histos[0]):
      histo.SetTitle('')
      histo.GetXaxis().SetTitle(self.texX)
      histo.GetYaxis().SetTitle(self.texY)
      if zRange is not None:
        histo.GetZaxis().SetRangeUser( *zRange )
      # precision 3 fonts. see https://root.cern.ch/root/htmldoc//TAttText.html#T5
      histo.GetXaxis().SetTitleFont(43)
      histo.GetYaxis().SetTitleFont(43)
      histo.GetXaxis().SetLabelFont(43)
      histo.GetYaxis().SetLabelFont(43)
      histo.GetXaxis().SetTitleSize(24)
      histo.GetYaxis().SetTitleSize(24)
      histo.GetXaxis().SetLabelSize(20)
      histo.GetYaxis().SetLabelSize(20)

      # should probably go into a styler

      histo.Draw(drawOption+same)
      same = "same"

    c1.RedrawAxis()

    if drawObjects:
      for o in drawObjects:
        try:    o.Draw()
        except: log.debug( "drawObjects has something I can't Draw(): %r", o)

    try:    os.makedirs(plot_directory)
    except: pass
    copyIndexPHP(plot_directory)

    copyGitInfo(os.path.join(plot_directory, self.name + '.gitInfo'))
    log.info('Creating output files for ' + self.name)
    for extension in (extensions if extensions else ["pdf", "png", "root","C"]):
      ofile = os.path.join( plot_directory, "%s.%s"%(self.name, extension) )
      c1.Print( ofile )
    del c1

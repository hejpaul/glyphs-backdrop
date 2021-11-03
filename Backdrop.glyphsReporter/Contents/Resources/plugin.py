# encoding: utf-8

from __future__ import division, print_function, unicode_literals
import objc
from GlyphsApp import *
from GlyphsApp.plugins import *
from vanilla import *
from AppKit import NSEvent, NSColor, NSAffineTransform, NSFontManager, NSFont, NSItalicFontMask, NSUnitalicFontMask, NSAttributedString

from glyphLib import standardGL

class Backdrop(ReporterPlugin):
	fallbackListItems = {"Visibility": False, "Status": None, "Name": "None", "Position": 0, "layer": None}
	@objc.python_method
	def settings(self):
		self.menuName = "Backdrop"
		self.currentWindow = None
		self.toolStatus = False
		self.alignment = 0
		self.listLength = 0

		Glyphs.addCallback(self.docActivated_, DOCUMENTACTIVATED)

	def docActivated_(self, i):
		if self.toolStatus:
			self.refreshGL()
			self.updateWindowUI()

	def willDeactivate(self):
		self.toolStatus = False
		try:
			self.currentWindow.close()
		except:
			pass
		self.currentWindow = None

	@objc.python_method
	def refreshGL(self):
		if Glyphs.font.userData["backdropGlyphLib"] == None:
			Glyphs.font.userData["backdropGlyphLib"] = standardGL
			
		self.glyphLib = Glyphs.font.userData["backdropGlyphLib"]

	@objc.python_method
	def openWindow(self):
		w = FloatingWindow((200, 242), title = "Backdrop", closable = False)
		w.glyphList = List((10, 10, -10, 160), [{"Visibility": False, "Status": None, "Name": "None", "Position": 0, "layer": None}], columnDescriptions = [{"title": "Visibility", "cell": CheckBoxListCell(), "width": 30}, {"title": "Status", "width": 20, "editable": False}, {"title": "Name", "width": 80, "editable": False}, {"title": "Position", "width": 30}, {"title": "layer", "width": -3, "editable": False}], showColumnTitles = False, rowHeight = 20, drawFocusRing = False, enableDelete = True, editCallback = self.listEdited)
		w.addGlyphButton = Button((10, 180, 90, 20), "Add Glyph", callback = self.glyphPopover)
		w.transLeftButton = Button((128, 180, 30, 20), u"←", callback = self.moveLeft)
		w.transRightButton = Button((160, 180, 30, 20), u"→", callback = self.moveRight)
		w.alignButton = SegmentedButton((10, 209, -7, 21), [dict(title = u"􀌀"), dict(title = u"􀌁"), dict(title = u"􀌂")], callback = self.changeAlignment, selectionStyle = "one")
		w.alignButton.set(self.alignment)
		w.open()

		fm = NSFontManager.sharedFontManager()
		systemFont = NSFont.systemFontOfSize_(NSFont.systemFontSize())
		self.italicFont = fm.fontWithFamily_traits_weight_size_(systemFont.fontName(), NSItalicFontMask, 5, systemFont.pointSize())
		self.boldFont = fm.fontWithFamily_traits_weight_size_(systemFont.fontName(), NSUnitalicFontMask, 8, systemFont.pointSize())

		self.currentWindow = w
		self.toolStatus = True
		try:
			self.currentGlyph = Glyphs.font.selectedLayers[0]
		except:
			pass
		
		self.refreshGL()
		self.updateWindowUI()

	@objc.python_method
	def getBoldString(self, s):
		return NSAttributedString.alloc().initWithString_attributes_(s, {NSFontAttributeName: self.boldFont})

	@objc.python_method
	def getItalicString(self, s):
		return NSAttributedString.alloc().initWithString_attributes_(s, {NSFontAttributeName: self.italicFont})

	@objc.python_method
	def drawFriends(self, layer):
		try:
			friends = self.currentWindow.glyphList.get()
		except:
			friends = None

		c = 0

		if friends:
			for friend in friends:
				if friend.get("Visibility", 0):
					g = friend["layer"]
					if g.completeBezierPath is not None:
						bP = g.completeBezierPath.copy()
						t = NSAffineTransform.transform()

						if self.alignment == 1:
							translateX = layer.width / 2.0 - g.width / 2.0 + friend["Position"]
						elif self.alignment == 2:
							translateX = layer.width - g.width + friend["Position"]
						else:
							translateX = int(friend["Position"])

						t.translateXBy_yBy_(translateX, 0.0)
						tM = t.transformStruct()
						bP.applyTransform_(tM)

						NSColor.colorWithDeviceRed_green_blue_alpha_(1.0, 0.73, c, 0.35).set()
						bP.fill()

						c = (c + 0.27) % 1.0
	
	@objc.python_method
	def background(self, layer):
		if not self.toolStatus: self.openWindow()
		
		try:
			if self.currentGlyph is not layer:
				self.currentGlyph = layer
				self.updateWindowUI()
		except:
			self.currentGlyph = None
			self.updateWindowUI()
		
		self.drawFriends(layer)

	@objc.python_method
	def listEdited(self, sender):
		editedCAndR = sender.getEditedColumnAndRow()
		n = self.currentGlyph.parent.name
		
		# user changed visibility or deleted row
		if editedCAndR[0] == -1:
			try:
				gl = self.glyphLib[n]
			except:
				gl = None
			
			friends = self.currentWindow.glyphList.get()
			
			# user deleted row
			if self.listLength != len(self.currentWindow.glyphList):
				self.listLength =- 1
				for i in range(len(gl)):
					if not any(e["Name"] == gl[i][0] for e in friends):
						gl.pop(i)

			# user changed visibility 
			else:
				for row in friends:
					if gl and row.get("Status", " ") == " ":
						for friend in gl:
							if friend[0] == row.get("Name", None): 
								friend[1] = row["Visibility"]
				self.drawFriends(Glyphs.font.selectedLayers[0])
				Glyphs.redraw()

		# user changed position
		elif editedCAndR[0] == 3:
			sl = Glyphs.font.selectedLayers[0]
			changedRow = self.currentWindow.glyphList.get()[editedCAndR[1]]

			try:
				gl = self.glyphLib[n]
			except:
				gl = None
			
			if gl and changedRow["Status"] == " ":
				for friend in gl:
					if friend[0] == changedRow["Name"]:
						try:
							friend[2] = int(changedRow["Position"])
						except:
							Glyphs.showNotification("Change Position", "Invalid Input")
							self.updateWindowUI()
			self.drawFriends(sl)
			Glyphs.redraw()

	@objc.python_method
	def changeAlignment(self, sender):
		self.alignment = sender.get()
		self.drawFriends(Glyphs.font.selectedLayers[0])
		Glyphs.redraw()

	@objc.python_method
	def moveGlyph(self, amount):
		selections = self.currentWindow.glyphList.getSelection()

		editCallback = self.currentWindow.glyphList._editCallback
		self.currentWindow.glyphList._editCallback = None
		try:
			selectedLayer = Glyphs.font.selectedLayers[0]
		except:
			return # TODO: better error handling?
		for i in selections:
			row = self.currentWindow.glyphList[i]
			row["Position"] = int(row["Position"]) + amount
			try:
				gl = self.glyphLib[self.currentGlyph.parent.name]
			except:
				gl = None
			if gl:
				for friend in gl:
					if friend[0] == row["Name"]: friend[2] = int(row["Position"])
			self.drawFriends(selectedLayer)
			Glyphs.redraw()

		self.currentWindow.glyphList._editCallback = editCallback

	@objc.python_method
	def moveLeft(self, sender):
		shiftKeyPressed = NSEvent.modifierFlags() & 1 << 17 == 1 << 17
		if shiftKeyPressed:
			self.moveGlyph(-10)
		else:
			self.moveGlyph(-1)

	@objc.python_method
	def moveRight(self, sender):
		shiftKeyPressed = NSEvent.modifierFlags() & 1 << 17 == 1 << 17
		if shiftKeyPressed:
			self.moveGlyph(10)
		else:
			self.moveGlyph(1)
	
	@objc.python_method
	def updateWindowUI(self):
		if not self.currentGlyph:
			return
		
		n = self.currentGlyph.parent.name
		font = Glyphs.font
		try:
			gl = self.glyphLib[n]
		except:
			gl = None

		editCallback = self.currentWindow.glyphList._editCallback
		self.currentWindow.glyphList._editCallback = None

		self.currentWindow.glyphList.set([])

		try:
			gLayers = self.currentGlyph.layers
		except:
			gLayers = None
		try:
			currentLayerId = font.selectedLayers[0].layerId
		except:
			return # TODO: better error handling
		if gLayers and len(gLayers) > 1:
			for l in gLayers:
				if l is not selectedLayers[0]:
					self.currentWindow.glyphList.append({"Visibility": False, "Status": "􀐜", "Name": self.getBoldString(str(l.name)), "Position": 0, "layer": l})

		for g in font.glyphs:
			if g.name.startswith(n + "."):
				self.currentWindow.glyphList.append({"Visibility": False, "Status": "􀍡", "Name": self.getItalicString(str(g.name)), "Position": 0, "layer": g.layers[currentLayerId]})

		if gl:
			for friend in gl:
				friendLayer = font.glyphs[friend[0]].layers[currentLayerId]
				if friendLayer is not None:
					self.currentWindow.glyphList.append({"Visibility": friend[1], "Status": " ", "Name": friend[0], "Position": friend[2], "layer": friendLayer})
		
		self.currentWindow.glyphList._editCallback = editCallback

		self.listLength = len(self.currentWindow.glyphList)

	@objc.python_method
	def addGlyphButtonPressed(self, sender):
		n = self.currentGlyph.parent.name

		self.currentPop.close()
		newGlyph = Glyphs.font.glyphs[self.currentPop.searchTF.get()]

		if newGlyph is not None:
			if n in self.glyphLib:
				self.glyphLib[n].append([newGlyph.name, True, 0])
			else:
				self.glyphLib[n] = [[newGlyph.name, True, 0]]
			self.updateWindowUI()
			self.drawFriends(Glyphs.font.selectedLayers[0])
			Glyphs.redraw()
		else:
			Glyphs.showNotification("Add Glyph", "Glyph not found")

	@objc.python_method
	def glyphPopover(self, sender):
		pop = Popover((220, 40))
		pop.searchTF = EditText((9, 9, 140, 22), sizeStyle = "regular", continuous = False)
		pop.searchTF.selectAll()
		pop.addButton = Button((160, 10, 50, 20), "Add", callback = self.addGlyphButtonPressed)
		pop.open(parentView = sender, preferredEdge = "top")

		self.currentPop = pop

	@objc.python_method
	def __file__(self):
		"""Please leave this method unchanged"""
		return __file__

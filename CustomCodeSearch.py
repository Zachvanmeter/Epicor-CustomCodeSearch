from os import path, makedirs
from tkinter import *

import pyodbc

# pyinstaller -F --icon="EpicorSearchIcon.ico" "CustomCodeSearch.py"

# ######################################### #
#############################################
# ######################################### #

		# KNOBS TO TURN / SETTINGS #
			
REPLACEDICT = \
{		# because apparently I dont know how to use .decode()
	'&#x0A;':'\n'
	,'&amp;':'&'
	,'&quot;':'"'
	,'&#x0D;':''
	,'&#x09;':'\t'
	,'&gt;':'>'
	,'&lt;':'<'
	,'&le;':'≤'
	,'&ge;':'≥'
}

DEFAULT_SERVER = 'TMFSVR10'
DEFAULT_DATABASE = 'EpicorERP'

# ######################################### #
#############################################
# ######################################### #

def GenDefaultList(Server,Database):
	conn = pyodbc.connect('Driver={SQL Server};'
							  'Server='+Server+';'
							  'Database='+Database+';'
							  'Trusted_Connection=yes;')
	cursor = conn.cursor()
	cursor.execute(('SELECT '
		+'         Menu.MenuID '
		+'        ,Menu.Arguments '
		
		+'FROM     <DatabaseName>.Ice.Menu as Menu '
		
		).replace('<DatabaseName>',Database))
	DefaultList = []
	for row in cursor:
		MenuID, Arguments = row
		if '-c ' in Arguments:
			line = Arguments.split('-c ')[1]
			Name = line.split(' ')[0]
			if not Name in DefaultList:
				DefaultList.append(Name)
	return DefaultList

def GenCustomizationDict(Server,Database,q1,q2,NotClause,IgnrComt,Output,ShowCode,CustomDefault):
	conn = pyodbc.connect('Driver={SQL Server};'
							  'Server='+Server+';'
							  'Database='+Database+';'
							  'Trusted_Connection=yes;')
	cursor = conn.cursor()
	cursor.execute(('SELECT '
		+'         XXXDef.Key1 '
		+'        ,XXXDef.Key2 '
		+'        ,XXXDef.Content '
		
		+'FROM     <DatabaseName>.Ice.XXXDef as XXXDef '
		+"WHERE    XXXDef.TypeCode = 'Customization' "
		
		).replace('<DatabaseName>',Database))
	DefaultList = GenDefaultList(Server,Database)
	CustomizationDict = {}
	CustCount = 0 
	CustTotal = 0
	IsDefault = False
	for row in cursor:
		Name, Form, Content = row
		IsDefault = False
		if '<PropertyName>Script</PropertyName>' in Content:
			Script = Content.split('<PropertyName>Script</PropertyName>')[1]
			Script = Script.split('</PropertyValue>')[0]
			Script = Script.replace("    <PropertyValue>",'')
			CustomizationDict[Name] = {'Name':Name,'Form':Form,'Script':Script}
			
			if Name in DefaultList:
				IsDefault = True
				
			Header = '\n########################\n\n'+Name+' # Customization for '+Form
			Detail = '\t\t\tDefault\n' if IsDefault else '\t\t\tNot Default\n'
			Footer = '\n########################\n\n'
			
			if CustomDefault == 0 and IsDefault == False:
				continue
			CustTotal+=1
				
			if FindQ(q1,q2,NotClause,Script):
				print(Header)
				print(Detail)
				if ShowCode == 0: 
					PrintMatchingLines(q1,IgnrComt,CustCount,Script.split('\n'))
				else: 
					print(Script)
				print(Footer)
				CustCount += 1
				
				
			
			if Output == 1: FileHandler(Name,Script)
	print('\nSearch Complete for "%s". %s/%s Customizations Displayed\n'%(q1,CustCount,CustTotal))

def GenBPMCode(Server,Database,q1,q2,NotClause,IgnrComt,Output,ShowCode,IndexEnable,IncludeBase):
	def IsOkay(IndexEnable,IsEnabled):	
		if IndexEnable == 0 :
			if not IsEnabled:
				return False
			else:
				return True
		elif IndexEnable == 1:
			return True
		elif IndexEnable == 2:
			if not IsEnabled:
				return True
			else:
				return False
	def IsBase(IncludeBase,Name,DirectiveType):
		if IncludeBase == 0:
			if 'BASE' in Name or DirectiveType == 'OutOfTrans':
				return False
			else:
				return True
		elif IncludeBase == 1:
			return True
		elif IncludeBase == 2:
			if 'BASE' in Name or DirectiveType == 'OutOfTrans':
				return True
			else:
				return False
	def CleanBody(Body):
		Body = Body.encode('latin1', errors='ignore').decode('unicode_escape', errors='ignore')
		for k,v in REPLACEDICT.items():
			Body = Body.replace(k,v)
		return Body
	def GenCustomCode(Body):
		head,sep,tail = Body.partition('" Code="')
		Code,sep,tail = tail.partition('" ExecutionRule="')
		return Code
		# ###################################### #
	conn = pyodbc.connect('Driver={SQL Server};'
						  'Server='+Server+';'
						  'Database='+Database+';'
						  'Trusted_Connection=yes;')
	cursor = conn.cursor()
	cursor.execute(('SELECT '
		+'         BpDirective.BpMethodCode, '
		+'         BpDirectiveType.Name, '
		+'         BpDirective.Name, '
		+'         BpDirective.Body, '
		+'         BpDirective.IsEnabled '
		+'FROM     <DatabaseName>.Ice.BpDirective as BpDirective '
		+'INNER JOIN '
		+'         <DatabaseName>.Ice.BpDirectiveType as BpDirectiveType '
		+'      ON BpDirectiveType.Source = BpDirective.Source '
		+'     AND BpDirectiveType.DirectiveType = BpDirective.DirectiveType '
		).replace('<DatabaseName>',Database))
	print('Generating BPM Output...\n')
	BpmCount = 0 
	BpmTotal = 0

	for row in cursor:
		BpMethodCode,DirectiveType,Name,Body,IsEnabled = row
		Okay = IsOkay(IndexEnable,IsEnabled)
		Base = IsBase(IncludeBase,Name,DirectiveType)
	
		if Body and Okay and Base:
			BpmTotal += 1
			Body = CleanBody(Body)
			Code = GenCustomCode(Body)
			
			Header = '\n########################\n\n'+DirectiveType+' # '+BpMethodCode+' '+Name
			Detail = '\t\t\tEnabled\n' if IsEnabled else '\t\t\tDisabled\n'
			Footer = '\n########################\n\n'
			
			
			if FindQ(q1,q2,NotClause,Body):
				print(Header)
				print(Detail)
				if ShowCode == 0: PrintMatchingLines(q1,IgnrComt,BpmCount,Code.split('\n'))
				if ShowCode == 1: print(Code)
				if ShowCode == 2: print(Body)
				print(Footer)
				BpmCount += 1
			elif q1.upper() in Name.upper():
				print(Header+'\n'+Detail+'\nSearch Clause exists in BPM Name\n'+Footer)
				BpmCount += 1
			if Output == 1: FileHandler(BpMethodCode,Body)
	
	print('\nSearch Complete for "%s". %s/%s BPMs Displayed\n'%(q1,BpmCount,BpmTotal))

def FindQ(q1,q2,NotClause,Code):
		if q2 != '':
			qFound = (q1.upper() in Code.upper() and (NotClause == (q2.upper() in Code.upper())))
		else:
			qFound = (q1.upper() in Code.upper())
		return qFound	

def FileHandler(Name,Code):
	Filename = 'BPMs/'+Name+'.txt'	
	filepath,sep,name = Filename.rpartition('/')
	if not path.isdir(filepath):
		makedirs(filepath+'/')
	with open(Filename, 'w') as f:
		f.write(Code)
		
def PrintMatchingLines(q1,IgnrComt,BpmCount,lines):
	def CleanLine(line):
		while line[0] == ' ' or line[0] == '\t':
			line = line[1:]
		return line
	# ################################ #
	p = 0
	if not q1 == '':
		for i, line in enumerate(lines):
		
			if not IgnrComt: 
				Goodline = line.split('//')[0]
			else:
				Goodline = line
				
			if q1.upper() in Goodline.upper():
				print('Line:'+str(i+1)+' | '+CleanLine(line))
				p = 1
			elif q1.upper() in line.upper():
				p = 2
				
		if p == 0:	print('Search Clause exists in Widget')
		if p == 1:	pass # prints the line as above
		if p == 2:	print('Search Clause exists in Comment')


class SQLSearchTool:
	def __init__(self,master):
		self.master = master
		w,h = 533,293
		master.geometry('%dx%d'%(w,h))
		
		self.BF = ('Consolas 10')
		self.bg = Canvas(master, bd=0, highlightcolor='Gray94', width=w,height=h)
		self.bg.place(x=10,y=10)
		
		self.DeclareVars()
		self.BuildFrame()
		
	def DeclareVars(self):
		self.Buttons = {}
		self.Output = IntVar()
		self.IndexEnable = IntVar()
		self.ShowCode = IntVar()
		self.IncludeBase = IntVar()
		self.IgnrComt = IntVar()
		self.NotClause = IntVar()
		self.CustomDefault = IntVar()
		self.UseBPMS = IntVar()
		self.UseCust = IntVar()
		
		self.q1 = StringVar()
		self.q2 = StringVar()
		self.q1.set('')
		self.q2.set('')
		self.Server = StringVar()
		self.Server.set(DEFAULT_SERVER)
		self.Database = StringVar()
		self.Database.set(DEFAULT_DATABASE)
		
		self.Output.set(0)		    # 0,1
		self.IndexEnable.set(0)		# 0,1,2
		self.ShowCode.set(0)		# 0,1,2,3
		self.IncludeBase.set(0)		# 0,1,2
		self.IgnrComt.set(0)		# 0,1
		self.NotClause.set(0)		# 0,1
		self.CustomDefault.set(0)	# 0,1
		self.UseBPMS.set(1)			# 0,1
		self.UseCust.set(1)			# 0,1
		
	def BuildFrame(self):
			# Output Line type
		self.ShowCCan = Canvas(self.bg, bg='Gray75', width=100,height=500)
		self.master.bind("<Return>", self.SearchWrapper)
		self.ShowCCan.place(x=2,y=2)
		Label(self.ShowCCan, text='Output Content', anchor=W).pack(fill=X)
		Radiobutton(self.ShowCCan, font=self.BF, text='Lines                ', variable=self.ShowCode, value=0).pack()
		Radiobutton(self.ShowCCan, font=self.BF, text='Custom Code          ', variable=self.ShowCode, value=1).pack()
		Radiobutton(self.ShowCCan, font=self.BF, text='Entire BPM           ', variable=self.ShowCode, value=2).pack()
		Label(self.ShowCCan, font=self.BF, text='                        ').pack()
		Label(self.ShowCCan, font=self.BF, text='                        ').pack()
		Label(self.ShowCCan, font=self.BF, text='                        ').pack()
		Checkbutton(self.ShowCCan, font=self.BF, text='Write to File        ', variable=self.Output).pack()
		Checkbutton(self.ShowCCan, font=self.BF, text='Yield Comments       ', variable=self.IgnrComt).pack()
		Checkbutton(self.ShowCCan, font=self.BF, text='Search BPMs          ', variable=self.UseBPMS).pack()
		Checkbutton(self.ShowCCan, font=self.BF, text='Search Customizations',variable=self.UseCust).pack()
		
			# Server Settings
		Label(self.bg, text='Server', anchor=W).place(x=160,y=2)
		Entry(self.bg, font=self.BF,  width=12, textvariable=self.Server).place(x=200,y=4)
		Label(self.bg, text='Database', anchor=W).place(x=290,y=2)
		Entry(self.bg, font=self.BF,  width=18, textvariable=self.Database).place(x=345,y=4)
        
			# BPM Filters
		self.BPMCanvasOutline = Canvas(self.bg, bg='Gray60', width=356,height=111)
		self.BPMCanvasOutline.place(x=150,y=30)
		self.BPMCanvas = Canvas(self.BPMCanvasOutline, width=350,height=105)
		self.BPMCanvas.place(x=3,y=3)
				# Left Column
		self.InBseCan = Canvas(self.BPMCanvas, width=100,height=500)
		self.InBseCan.place(x=5,y=5)
		Label(self.InBseCan, text='BPM Filters', anchor=W).pack(fill=X)
		Radiobutton(self.InBseCan, font=self.BF, text='Custom BPMs         ', variable=self.IncludeBase, value=0).pack()
		Radiobutton(self.InBseCan, font=self.BF, text='Custom and Base BPMs', variable=self.IncludeBase, value=1).pack()
		Radiobutton(self.InBseCan, font=self.BF, text='Base BPMs           ', variable=self.IncludeBase, value=2).pack()
				# Right Column
		self.NAbleCan = Canvas(self.BPMCanvas, width=100,height=500)
		self.NAbleCan.place(x=175,y=5)
		Label(self.NAbleCan, text='', anchor=W).pack(fill=X)
		Radiobutton(self.NAbleCan, font=self.BF, text='Enabled             ', variable=self.IndexEnable, value=0).pack()
		Radiobutton(self.NAbleCan, font=self.BF, text='Enabled and Disabled', variable=self.IndexEnable, value=1).pack()
		Radiobutton(self.NAbleCan, font=self.BF, text='Disabled            ', variable=self.IndexEnable, value=2).pack()
			
			# Customization Filters
		self.CustomCanvasOutline = Canvas(self.bg, bg='Gray60', width=356,height=80)
		self.CustomCanvasOutline.place(x=150,y=150)
		self.CustomCanvas = Canvas(self.CustomCanvasOutline, width=350,height=74)
		self.CustomCanvas.place(x=3,y=3)
				# Options
		self.CustomCan = Canvas(self.CustomCanvas, bg='Gray60',width=100,height=500)
		self.CustomCan.place(x=5,y=5)
		Label(self.CustomCan, text='Customization Filters', anchor=W).pack(fill=X)
		Radiobutton(self.CustomCan, font=self.BF, text='Is Default   ', variable=self.CustomDefault, value=0).pack()
		Radiobutton(self.CustomCan, font=self.BF, text='All          ', variable=self.CustomDefault, value=1).pack()
		
		y=245
			# Entry Boxes and Search Button
		Entry(self.bg, font=self.BF,  width=12, textvariable=self.q1).place(x=200,y=y)
		self.NotChk = Checkbutton(self.bg,  font=self.BF, variable=self.NotClause)
		self.NotChk.place(x=310,y=y)
		Entry(self.bg, font=self.BF,  width=12, textvariable=self.q2).place(x=360,y=y)
		Button(self.bg,font=self.BF,  text='Search', command=self.SearchWrapper).place(x=455,y=y-5)
		
		self.Update()
		
	def SearchWrapper(self, Event=None):
		Server = self.Server.get()
		Database = self.Database.get()
		q1 = self.q1.get()
		q2 = self.q2.get()
		NotClause = True if self.NotClause.get() == 0 else False
		IgnrComt = False if self.IgnrComt.get() == 0 else True
		Output = self.Output.get()
		ShowCode = self.ShowCode.get()
		IndexEnable = self.IndexEnable.get()
		IncludeBase = self.IncludeBase.get()
		if self.UseBPMS.get() == 1:
			print('################################################################')
			print('######################## # #  BPMS  # # ########################')
			print('################################################################')
			GenBPMCode(
				Server,Database,q1,q2,NotClause,IgnrComt,Output,ShowCode,IndexEnable,IncludeBase
				)
		CustomDefault = self.CustomDefault.get()
		if self.UseCust.get() == 1:
			print('################################################################')
			print('######################## Customizations ########################')
			print('################################################################')
			GenCustomizationDict(
				Server,Database,q1,q2,NotClause,IgnrComt,Output,ShowCode,CustomDefault
				)

	def Update(self):
		if   self.NotClause.get() == 0:
			self.NotChk.config(text=r'& ')
		elif self.NotClause.get() == 1:
			self.NotChk.config(text=r'&!')
		self.master.after(500,self.Update)
		
def RunUI():
	root = Tk()
	root.title('CustomCodeSearch')
	app = SQLSearchTool(root)
	root.mainloop()
	
if __name__ == '__main__':
	RunUI()
	
		

import os
import sys
import optparse
import subprocess
import json
import ROOT
from collections import OrderedDict

def prepare_range(path, fin):
  try:
    f_read = ROOT.TFile.Open(path + fin)
    entries = (f_read.Get('Events')).GetEntriesFast()
    step = 750000
    init = 0
    index = []
    while(init < entries):
      index.append(init)
      init += step
    index.append(int(entries))
    f_read.Close()
    return index
  except:
    print("%s%s fail to process."%(path,fin))
    return None
def prepare_shell(era, isMC, trig_sf, cfsf, shift, fin, xs, start, end, label, FarmDir,condor):
  cmsswBase = os.environ['CMSSW_BASE']
  shell_name = era + "_" + str(cfsf) + str(shift) + fin + str(label) + ".sh"
  with open('%s/%s'%(FarmDir,shell_name),'w') as shell:
    shell.write('#!/bin/bash\n')
    shell.write('WORKDIR=%s/src/MuonIDScaleFactor_Plot\n'%cmsswBase)
    shell.write('cd %s\n'%cmsswBase)
    shell.write('eval `scram r -sh`\n')
    shell.write('cd ${WORKDIR}\n')
    shell.write('python %s/src/MuonIDScaleFactor_Plot/flatten.py '%cmsswBase)
    shell.write('--era %s '%era)
    shell.write('--isMC %d '%isMC)
    shell.write('--trig %d '%trig_sf)
    shell.write('--fin %s '%fin)
    shell.write('--xsec %f '%xs)
    shell.write('--cfsf %d '%cfsf)
    shell.write('--shift %d '%shift)
    shell.write('--from %d '%start)
    shell.write('--to %d '%end)
    shell.write('--label %d '%label)
  condor.write('cfgFile=%s\n'%shell_name)
  condor.write('queue 1\n') 

if __name__=='__main__':
  FarmDir = os.environ['CMSSW_BASE'] + "/Farm_muon_plot/"
  os.system('mkdir -p %s'%FarmDir)
  os.system('rm %s/*'%FarmDir)
  directory = ["NotApplyChargeFlipsf_Nominal"] #, "NotApplyChargeFlipsf_Nominal", "ApplyChargeFlipsf_UP", "ApplyChargeFlipsf_DOWN"]
  condor = open('%s/condor.sub'%FarmDir,'w')
  condor.write('output = %s/job_common.out\n'%FarmDir)
  condor.write('error  = %s/job_common.err\n'%FarmDir)
  condor.write('log    = %s/job_common.log\n'%FarmDir)
  condor.write('executable = %s/$(cfgFile)\n'%FarmDir)
  condor.write('requirements = (OpSysAndVer =?= "CentOS7")\n')
  condor.write('+JobFlavour = "tomorrow"\n')
  condor.write('+MaxRuntime = 7200\n')

#  Eras = ['2016postapv','2016apv','2017','2018']
  Eras = ['2018']
  trigger_sf = 0
  chargeflip_sf =[(0,0)] #,(0,0),(1,1),(1,-1)]
  for era in Eras:
    for di in directory:
      os.system('mkdir -p flatten/era%s/%s'%(era,di))
      os.system('rm flatten/era%s/%s/*'%(era,di))
    if(era == "2017"):
      path = '/eos/cms/store/group/phys_top/ExtraYukawa/TTC_version9/'
    elif(era == '2018'):
      path = '/eos/cms/store/group/phys_top/ExtraYukawa/2018/'
    elif(era == '2016postapv'):
      path = '/eos/cms/store/group/phys_top/ExtraYukawa/2016postapvMerged/'
    elif(era == '2016apv'):
      path = '/eos/cms/store/group/phys_top/ExtraYukawa/2016apvMerged/'


    jsonfile = open(os.path.join('data/sample_' + era + 'UL.json'))
    samples = json.load(jsonfile, encoding='utf-8', object_pairs_hook=OrderedDict).items()
    jsonfile.close()

    for process, desc in samples:
      dirs = os.listdir(path)
      for f in dirs:
        if((desc[1] and process == f.replace('.root','')) or (not desc[1] and process in f)):
          print(f)
          range_list = prepare_range(path,f)
          if(range_list is None):
            continue
          for i in range(len(range_list)-1):
            start = range_list[i]
            end = range_list[i+1]
            for cfsf,shift in chargeflip_sf:
              prepare_shell(era,desc[1],trigger_sf,cfsf,shift,f,desc[0],start,end,i, FarmDir,condor)
  condor.close()
  os.system('condor_submit %s/condor.sub'%FarmDir)


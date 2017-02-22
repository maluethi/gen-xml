import definitions as de
import argparse

try:
    import project_utilities as pu
except ImportError as e:
    print("root is unavalable")

parser = argparse.ArgumentParser(description='XML file creator to extract timestamps based on run number')
parser.add_argument('run_number', type=int, help='uboone run number')
parser.add_argument('-o', dest='out_dir', default='', type=str, help='output directory')
parser.add_argument('-d', dest='sam_definition', default=None, type=str, help='predefined sam definition to be used')
args = parser.parse_args()

run_number = args.run_number
output_dir = args.out_dir

# SAM generation / checks
sam_num_jobs = 0
sam = []
try:
    sam = pu.samweb()
except NameError as e:
    print e

if not args.sam_definition:
    sam_rundef = "laser-" + str(run_number)
    sam.createDefinition(defname=sam_rundef,
                         dims="run_number=" + str(run_number) + " and data_tier=raw and file_format=artroot"
                         )
else:
    sam_rundef = args.sam_definition

sam_num_jobs = sam.countFiles(defname=sam_rundef)

# base dirs
out_dir_base = "/pnfs/uboone/scratch/users/maluethi/"
work_dir_base = "/uboone/app/users/maluethi/"
log_dir_base = "/uboone/data/users/maluethi/"

init_script_dir = "/uboone/app/users/maluethi/laser/grid/"

fcl_top_dir = "/uboone/app/users/maluethi/laser/fcl/"

# XML generation
job_name = "laser-reco"
run_name = "laser-" + str(run_number) + "/"

xml_file = job_name + "-" + str(run_number) + ".xml"

# Stage 1
stage_name = "reco"
out_dir = out_dir_base + stage_name + "/" + run_name
work_dir = work_dir_base + stage_name + "/" + run_name
log_dir = log_dir_base + stage_name + "/" + run_name + "log/"

proj = de.Project("laser-reco",
                  fcldir=fcl_top_dir
                  )
stage1 = de.Stage(stage_name,
                  "laser_reco_50kV.fcl",
                  num_jobs=sam_num_jobs,
                  datatier="raw",
                  outdir=out_dir,
                  logdir=log_dir,
                  workdir=work_dir,
                  inputdef=sam_rundef,
                  defname=stage_name,
                  )
# stage 2
stage_name = "merger"
out_dir = out_dir_base + stage_name + "/" + run_name
work_dir = work_dir_base + stage_name + "/" + run_name
log_dir = log_dir_base + stage_name + "/" + run_name + "log/"

init_script = "copy-script-" + str(run_number) + ".sh"

stage2 = de.Stage(stage_name,
                  "LaserDataMerger.fcl",
                  num_jobs=sam_num_jobs,
                  outdir=out_dir,
                  logdir=log_dir,
                  workdir=work_dir,
                  initscript= init_script_dir + init_script)


# stage 3
stage_name = "get-tracks"
out_dir = out_dir_base + stage_name + "/" + run_name
work_dir = work_dir_base + stage_name + "/" + run_name
log_dir = log_dir_base + stage_name + "/" + run_name + "log/"

stage3 = de.Stage(stage_name,
                  "get_tracks.fcl",
                  num_jobs=sam_num_jobs,
                  outdir=out_dir,
                  logdir=log_dir,
                  workdir=work_dir,
                  )



larsoft_dir = "/uboone/app/users/maluethi/laser/v06_20_00/locale.tar"
larsoft = de.Larsoft("v06_20_00", "e9:prof", local_larsoft=larsoft_dir)

print("fuck this")

proj.add_larsoft(larsoft)
proj.add_stage(stage1)
proj.add_stage(stage2)
proj.add_stage(stage3)

proj.gen_xml()
proj.write_xml(output_dir + xml_file)

# lets generate the init script:

TimeMap =  ["/uboone/app/users/maluethi/timemap/TimeMap/", "TimeMap-" + str(run_number) + ".root"]
WireMap = ["/uboone/app/users/maluethi/laser/laserdata/", "WireIndexMap.root"]
LaserData = ["/uboone/app/users/maluethi/laser/laserdata/", "Run-" + str(run_number) + ".txt"]

to_copy = [TimeMap, WireMap, LaserData]

setup = "setup ifdhc"
cp_command = "ifdh cp "
with open(output_dir + init_script, "wr") as file:
    file.write("#!/bin/bash\n")
    file.write("\n")
    file.write(setup + "\n")
    file.write("\n")
    for entry in to_copy:
        file.write(cp_command + entry[0] + entry[1] + " ./" + entry[1] + "\n")

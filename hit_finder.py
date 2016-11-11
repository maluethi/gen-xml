import definitions as de

try:
    import project_utilities as pu
except ImportError as e:
    print("root is unavalable")

run_number = 7206
sam_num_jobs = 0
# SAM generation / checks
sam_rundef = "laser_run-" + str(run_number)

try:
    sam = pu.samweb()
    sam.createDefinition(defname=sam_rundef,
                         dims="run_number=" + str(run_number) + " and data_tier=raw and file_format=artroot"
                         )
    sam_num_jobs = sam.countFiles(defname=sam_rundef)
except NameError as e:
    print e

# XML generation
job_name = "laser-hit-finder"
run_name = "laser-" + str(run_number) + "/"

xml_file = job_name + "-" + str(run_number) + ".xml"

out_dir = "/pnfs/uboone/scratch/users/maluethi/" + job_name + "/" + run_name
work_dir = "/uboone/app/users/maluethi/" + job_name + "/" + run_name
log_dir = "/uboone/app/users/maluethi/" + job_name + "/" + run_name + "log/"

fcl_top_dir = "/uboone/app/users/maluethi/laser/fcl/"

init_script = "copy-script-" + str(run_number) + ".sh"
init_script_dir = "/uboone/app/users/maluethi/laser/grid/"
proj = de.Project(job_name,
                  fcldir=fcl_top_dir
                  )
stage1 = de.Stage(job_name,
                  "laser_hitana.fcl",
                  num_jobs=sam_num_jobs,
                  datatier="raw",
                  outdir=out_dir,
                  logdir=log_dir,
                  workdir=work_dir,
                  defname=sam_rundef,
                  initscript=init_script_dir + init_script
                  )

larsoft_dir = "/uboone/app/users/maluethi/laser/v05_08_00/locale.tgz"
larsoft = de.Larsoft("v05_08_00", "e9:prof", local_larsoft=larsoft_dir)

print("fuck this")

proj.add_larsoft(larsoft)
proj.add_stage(stage1)
proj.gen_xml()
proj.write_xml(xml_file)

# lets generate the init script:

TimeMap = ["/uboone/app/users/maluethi/laser/timemap/TimeMap/", "TimeMap-" + str(run_number) + ".root"]
WireMap = ["/uboone/app/users/maluethi/laser/laserdata/","WireIndexMap.root"]
LaserData = ["/uboone/app/users/maluethi/laser/laserdata/", "Run-" + str(run_number) + ".txt"]

to_copy = [TimeMap, WireMap, LaserData]

setup = "setup ifdhc"
cp_command = "ifdh cp "
with open(init_script, "wr") as file:
    file.write("#!/bin/bash\n")
    file.write("\n")
    file.write(setup + "\n")
    file.write("\n")
    for entry in to_copy:
        file.write(cp_command + entry[0] + entry[1] + " ./" + entry[1] + "\n")

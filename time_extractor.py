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
job_name = "time-extractor"
run_name = "laser-" + str(run_number) + "/"

xml_file = job_name + "-" + str(run_number) + ".xml"

work_dir = "/pnfs/uboone/scratch/users/maluethi/" + job_name + "/" + run_name
out_dir = "/uboone/app/users/maluethi/" + job_name + "/" + run_name
log_dir = "/uboone/app/users/maluethi/" + job_name + "/" + run_name + "log/"

proj = de.Project("123")
stage1 = de.Stage(job_name,
                  "TimeMapProducer.fcl",
                  num_jobs=sam_num_jobs,
                  datatier="raw",
                  outdir=out_dir,
                  logdir=log_dir,
                  workdir=work_dir,
                  defname=sam_rundef
                  )

larsoft_dir ="/uboone/app/users/maluethi/laser/v05_14_01/local.tgz"
larsoft = de.Larsoft("v05_14_01", "e9:prof", local_larsoft=larsoft_dir)

print("fuck this")

proj.add_larsoft(larsoft)
proj.add_stage(stage1)
proj.gen_xml()
proj.write_xml(xml_file)

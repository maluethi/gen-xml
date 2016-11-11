import definitions as de
import argparse

try:
    import project_utilities as pu
except ImportError as e:
    print("root is unavalable")

parser = argparse.ArgumentParser(description='XML file creator to extract timestamps based on run number')
parser.add_argument('run_number', type=int, help='uboone run number')
args = parser.parse_args()                    

run_number = args.run_number


# SAM generation / checks
sam_num_jobs = 0
sam_rundef = "laser-" + str(run_number)

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

out_dir = "/pnfs/uboone/scratch/users/maluethi/" + job_name + "/" + run_name
work_dir = "/uboone/app/users/maluethi/" + job_name + "/" + run_name
log_dir = "/uboone/data/users/maluethi/" + job_name + "/" + run_name + "log/"

fcl_top_dir = "/uboone/app/users/maluethi/laser/fcl/"

proj = de.Project("time-extract",
				  fcldir=fcl_top_dir
				  )
stage1 = de.Stage(job_name,
                  "TimeMapProducer.fcl",
                  num_jobs=sam_num_jobs,
                  datatier="raw",
                  outdir=out_dir,
                  logdir=log_dir,
                  workdir=work_dir,
                  inputdef=sam_rundef,
                  defname=job_name
				  )

larsoft_dir ="/uboone/app/users/maluethi/laser/v05_14_01/local.tgz"
larsoft = de.Larsoft("v05_14_01", "e9:prof", local_larsoft=larsoft_dir)


proj.add_larsoft(larsoft)
proj.add_stage(stage1)
proj.gen_xml()

print("job submit file written to: " + str(xml_file) )
proj.write_xml(xml_file)

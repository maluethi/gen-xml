try:
  from lxml import etree
except ImportError:
  try:
    # Python 2.5
    import xml.etree.cElementTree as etree
    print("running with cElementTree on Python 2.5+")
  except ImportError:
    try:
      # Python 2.5
      import xml.etree.ElementTree as etree
      print("running with ElementTree on Python 2.5+")
    except ImportError:
      try:
        # normal cElementTree install
        import cElementTree as etree
        print("running with cElementTree")
      except ImportError:
        try:
          # normal ElementTree install
          import elementtree.ElementTree as etree
          print("running with ElementTree")
        except ImportError:
          print("Failed to import ElementTree from any known place")
import platform

class Project():
    ######################################################################
    #
    # XML file structure
    # ------------------
    #
    # The xml file must contain one or more elements with tag "project."
    #
    # The project element must have attribute "name."
    #
    # The following element tags withing the project element are recognized.
    #
    # <numevents> - Total number of events (required).
    # <numjobs> - Number of worker jobs (default 1).  This value can be
    #             overridden for individual stages by <stage><numjobs>.
    # <maxfilesperjob> - Maximum number of files to deliver to a single job
    #             Useful in case you want to limit output file size or keep
    #             1 -> 1 correlation between input and output. can be overwritten
    #             by <stage><maxfilesperjob>
    # <os>      - Specify batch OS (comma-separated list: SL5,SL6).
    #             Default let jobsub decide.
    # <server>  - Jobsub server (expert option, jobsub_submit --jobsub-server=...).
    #             If "" (blank), "-" (hyphen), or missing, omit --jobsub-server
    #             option (use default server).
    # <resource> - Jobsub resources (comma-separated list: DEDICATED,OPPORTUNISTIC,
    #              OFFSITE,FERMICLOUD,PAID_CLOUD,FERMICLOUD8G).
    #              Default: DEDICATED,OPPORTUNISTIC.
    # <lines>   - Arbitrary condor commands (expert option, jobsub_submit --lines=...).
    # <site>    - Specify site (default jobsub decides).
    #
    # <cpu>     - Number of cpus (jobsub_submit --cpu=...).
    # <disk>    - Amount of scratch disk space (jobsub_submit --disk=...).
    #             Specify value and unit (e.g. 50GB).
    # <memory>  - Specify amount of memory in MB (jobsub_submit --memory=...).
    #
    # <script>  - Name of batch worker script (default condor_lar.sh).
    #             The batch script must be on the execution path.
    #
    # <version> - Specify project version (default same as <larsoft><tag>).
    #
    # <filetype> - Sam file type ("data" or "mc", default none).
    # <runtype>  - Sam run type (normally "physics", default none).
    # <runnumber> - Sam run number (default nont).
    # <parameter name="parametername"> - Specify experiment-specific metadata parameters
    #
    def __init__(self,
                 name,
                 group="uboone",
                 numevents=1000000,
                 maxfilesperjob=1,
                 os="SL6",
                 filetype="data",
                 runtype="calibration",
                 resource = 'DEDICATED,OPPORTUNISTIC',
                 ):

        self.name = name
        self.group = group
        self.numevents = numevents
        self.maxfilesperjob = maxfilesperjob
        self.os = os
        self.filetype = filetype
        self.runtype = runtype
        self.resource = resource

        self.stages = []

        self.xml_root = None
        self.xml_larsoft = None
        self.xml_stages = []

        self.check_gpvm()

    def add_larsoft(self, larsoft):
        if not isinstance(larsoft, Larsoft):
            raise ValueError("Expected Larsoft object")
        if hasattr(self, "larsoft"):
            raise AttributeError("Larsoft definition already exists")

        setattr(self, "larsoft", larsoft)

    def add_stage(self, stage):
        if not isinstance(stage, Stage):
            raise ValueError("Expected Stage object")
        if stage.name in self.stages:
            raise ValueError(stage.name + " is already in stages")

        self.stages.append(stage.name)
        setattr(self, stage.name, stage)

    def remove_stage(self, stage):
        if getattr(self, stage):
            self.stages.remove(stage)
            delattr(self, stage)
        else:
            raise AttributeError("Unknown stage " + str(stage))

    def check_gpvm(self):
        if 'uboonegpvm' in platform.node():
            return True
        else:
            return False

    def gen_proj_xml(self):
        self.xml_root = etree.Element('project', name=self.name)
        for key, value in self.__dict__.items():
            if isinstance(value, (str, int, float)) and (key not in ["name", "outfile"]):
                etree.SubElement(self.xml_root, key).text = str(value)

    def gen_lar_xml(self):
        self.xml_larsoft = etree.SubElement(self.xml_root, 'larsoft')
        for key, value in self.larsoft.__dict__.items():
            if isinstance(value, (str, int, float)) and key is not "name":
                etree.SubElement(self.xml_larsoft, key).text = str(value)

    def gen_xml(self):
        self.gen_proj_xml()
        self.gen_lar_xml()
        self.gen_stage_xml()

    def gen_stage_xml(self):
        for idx, stage in enumerate(self.stages):
            self.xml_stages.append(etree.SubElement(self.xml_root, 'stage', name=stage))
            for key, value in getattr(self, stage).__dict__.items():
                if isinstance(value, (str, int, float)) and key is not "name":
                    etree.SubElement(self.xml_stages[idx], key).text = str(value)


    def write_xml(self, filename):
        with open(filename, "w+") as xmlfile:
            xmlfile.write(etree.tostring(self.xml_root, pretty_print=True))


class Stage(object):
    """'Lazy implementation of the stage requirements """

    # <stage name="stagename"> - Information about project stage.  There can
    #             be multiple instances of this tag with different name
    #             attributes.  The name attribute is optional if there is
    #             only one project stage.
    # <stage><fcl> - Name of fcl file (required).  Specify just the filename,
    #             not the full path.
    # <stage><outdir> - Output directory (required).  A subdirectory with the
    #             project name is created underneath this directory.  Individual
    #             workers create an additional subdirectory under that with
    #             names like <cluster>_<process>.
    # <stage><logdir> - Log directory (optional).  If not specified, default to
    #                   be the same as the output directory.  A directory structure
    #                   is created under the log directory similar to the one
    #                   under the output directory.
    # <stage><workdir> - Specify work directory (required).  This directory acts
    #             as the submission directory for the batch job.  Fcl file, batch
    #             script, and input file list are copied here.  A subdirectory with
    #             the name of the project and "/work" are appended to this path.
    #             This directory should be grid-accessible and located on an
    #             executable filesystem (use /expt/app rather than /expt/data).
    # <stage><inputfile> - Specify a single input file (full path).  The number
    #             of batch jobs must be one.
    # <stage><inputlist> - Specify input file list (a file containing a list
    #             of input files, one per line, full path).
    # <stage><inputmode> - Specify input file tyle. Default is none which means
    #             art root file. Alternative is textfile
    # <stage><inputdef>  - Specify input sam dataset definition.
    #
    #             It is optional to specify an input file or input list (Monte
    #             Carlo generaiton doesn't need it, obviously).  It is also
    #             optional for later production stages.  If no input is specified,
    #             the list of files produced by the previous production stage
    #             (if any) will be used as input to the current production stage
    #             (must have been checked using option --check).
    # <stage><inputstream> - Specify input stream.  This only effect of this
    #             parameter is to change the default input file list name from
    #             "files.list" to "files_<inputstream>.list."  This parameter has
    #             no effect if any non-default input is specified.
    # <stage><previousstage> - Specify the previous stage name to be something other
    #             than the immediate predecessor stage specified in the xml file.
    #             This parameter only affects the default input file list.  This
    #             parameter has no effect if any non-default input is specified.
    # <stage><mixinputdef> - Specify mix input from a sam dataset.
    # <stage><pubsinput> - 0 (false) or 1 (true).  If true, modify input file list
    #                      for specific (run, subrun, version) in pubs mode.  Default is true.
    # <stage><maxfluxfilemb> - Specify GENIEHelper fcl parameter MaxFluxFileMB.
    # <stage><numjobs> - Number of worker jobs (default 1).
    # <stage><numevents> - Number of events (override project level number of events).
    # <stage><maxfilesperjob> - Maximum number of files to deliver to a single job
    #             Useful in case you want to limit output file size or keep
    #             1 -> 1 correlation between input and output
    # <stage><targetsize> - Specify target size for output files.  If specified,
    #                       this attribute may override <numjobs> in the downward
    #                       direction (i.e. <numjobs> is the maximum number of jobs).
    # <stage><defname> - Sam output dataset defition name (default none).
    # <stage><anadefname> - Sam analysis output dataset defition name (default none).
    # <stage><datatier> - Sam data tier (default none).
    # <stage><anadatatier> - Sam analysis data tier (default none).
    # <stage><initscript> - Worker initialization script (condor_lar.sh --init-script).
    # <stage><initsource> - Worker initialization bash source script (condor_lar.sh --init-source).
    # <stage><endscript>  - Worker end-of-job script (condor_lar.sh --end-script).
    #                       Initialization/end-of-job scripts can be specified using an
    #                       absolute or relative path relative to the current directory.
    # <stage><merge>  - Name of special histogram merging program or script (default "hadd -T",
    #                       can be overridden at each stage).
    # <stage><resource> - Jobsub resources (comma-separated list: DEDICATED,OPPORTUNISTIC,
    #                     OFFSITE,FERMICLOUD,PAID_CLOUD,FERMICLOUD8G).
    #                     Default: DEDICATED,OPPORTUNISTIC.
    # <stage><lines>   - Arbitrary condor commands (expert option, jobsub_submit --lines=...).
    # <stage><site>    - Specify site (default jobsub decides).
    # <stage><cpus>    - Number of cpus (jobsub_submit --cpus=...).
    # <stage><disk>    - Amount of scratch disk space (jobsub_submit --disk=...).
    #                    Specify value and unit (e.g. 50GB).
    # <stage><memory>  - Specify amount of memory in MB (jobsub_submit --memory=...).
    # <stage><output>  - Specify output file name.
    # <stage><TFileName>   - Ability to specify unique output TFile Name
    #		         (Required when generating Metadata for TFiles)
    # <stage><jobsub>  - Arbitrary jobsub_submit option(s).  Space-separated list.
    #                    Only applies to main worker submission, not sam start/stop
    #                    project submissions.
    # <stage><maxfilesperjob> - Maximum number of files to be processed in a single worker.
    def __init__(self,
                 name,
                 fcl,
                 outdir=None,
                 logdir=None,
                 workdir=None,
                 inputdef=None,
                 datatier=None,
                 initscript=None,
                 num_jobs=None,
                 defname=None):
        self.name = name
        self.fcl = fcl
        if outdir is not None: self.outdir = outdir + name + "/"
        if logdir is not None: self.logdir = logdir + name + "/"
        if workdir is not None: self.workdir = workdir + name + "/"
        self.inputdef = inputdef
        self.initscript = initscript
        self.datatier = datatier
        self.numjobs = num_jobs
        self.defname = defname


class Larsoft(object):
    # <larsoft> - Information about larsoft release.
    # <larsoft><tag> - Frozen release tag (default "development").
    # <larsoft><qual> - Build qualifier (default "debug", or "prof").
    # <larsoft><local> - Local test release directory or tarball (default none).
    def __init__(self, version, qualifier, local_larsoft=None):
        self.tag = version
        self.qualifier = qualifier
        self.local= local_larsoft

if __name__ == "__main__":

    run_number = 123
    num_jobs = 88

    job_name = "test"
    run_name = "laser-" + str(run_number) + "/"

    work_dir = "/pnfs/uboone/scratch/users/maluethi/" + job_name + "/" + run_name
    out_dir = "/uboone/app/users/maluethi/" + job_name + "/" + run_name
    log_dir = "/uboone/app/users/maluethi/" + job_name + "/" + run_name + "log/"

    proj = Project("123")
    stage1 = Stage("stage1",
                   "fcl1.fcl",
                   num_jobs=num_jobs,
                   datatier="raw",
                   outdir=out_dir,
                   logdir=log_dir,
                   workdir=work_dir
                   )

    stage2 = Stage("stage2",
                   "fcl2.fcl",
                   num_jobs=num_jobs,
                   datatier="reconstructed",
                   outdir=out_dir,
                   logdir=log_dir,
                   workdir=work_dir)

    larsoft = Larsoft("v05_19_00", "e9:prof")

    proj.add_larsoft(larsoft)
    proj.add_stage(stage1)
    proj.add_stage(stage2)
    proj.gen_xml()
    print(etree.tostring(proj.xml_root, pretty_print=True))
    proj.write_xml("test.xml")

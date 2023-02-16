#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
import argparse
import os
import re
import subprocess
import sys
import traceback
from difflib import SequenceMatcher
from shutil import rmtree
from rich.console import Console, Text

console = Console()


class MyParser(argparse.ArgumentParser):
    """
    Convenience class for the ArgParse parser.
    """

    def error(self, message):
        console.print('error: %s' % message, style='red')
        self.print_help()
        sys.exit(2)


class ComponentGenerationChecker:
    """
    Class containing methods used to generate code and compile a bunch of components to be tested.
    """

    def __init__(self):
        self.results = {}
        self.valid = 0
        self.generated = 0
        self.compared = 0
        self.comp_failed = 0
        self.gen_failed = 0
        self.dry_run = False

    def generate_code(self, idsl_file, output_dir, dry_run=True):
        """
        Execution of the robocompdsl script to generate the component code for a gigen .idsl file.
        :param idsl_file: filename of the .idsl of the component to be generated
        :param log_file: name of the log file to be written with the result of the command execution.
        :param dry_run: Force to just show messages of what would be done but no command is executed.
        :return: command execution return code
        """
        ice_file = os.path.join(output_dir,os.path.splitext(os.path.basename(idsl_file))[0]+".ice")
        log_file = os.path.join(output_dir,os.path.splitext(os.path.basename(idsl_file))[0]+"_generation.log")
        if dry_run:
            print('robocompdsl %s %s > %s 2>&1' % (idsl_file, ice_file, log_file))
            return 0
        else:
            with open(log_file, "wb") as log:
                command_output = subprocess.Popen(
                    "python " + os.path.expanduser("/robocompdsl/robocompdsl/robocompdsl.py") + " %s %s" % (idsl_file, ice_file),
                    stdout=log,
                    stderr=log,
                    shell=True)
                stdout, stderr = command_output.communicate()
                # print(stdout)
                # print(stderr)
                return command_output.returncode, ice_file
            return -1, None

    def statistical_ice_file_comparation(self, first_file, second_file):
        """
        Compare two .ice files looking for differences. It's not a line by line comparation method. This is intended
        to find similarity on the contained code of the files to check generation. For this reason this method
        remove comments, empty lines, sort lines and look for the most similar line between the resulting ones.
        :param first_file:
        :param second_file:
        :return: number of different lines, lines differences, detect if the files are obsolete
        """
        # aux function to remove the c++ style comments
        def replacer(match):
            s = match.group(0)
            if s.startswith('/'):
                return " "  # note: a space and not an empty string
            else:
                return s
        # patter to detect c++ stule comments (// and /**/
        pattern = re.compile(
            r'//.*?$|/\*.*?\*/|\'(?:\\.|[^\\\'])*\'|"(?:\\.|[^\\"])*"',
            re.DOTALL | re.MULTILINE)
        n_diff_lines = -1
        diff_lines = []
        deprecated = True
        with open(first_file, "r") as file1:
            lines1 = file1.read()
            with open(second_file, "r") as file2:
                lines2 = file2.read()
                if "Generated by RoboCompDSL" in lines1 and "Generated by RoboCompDSL" in lines2:
                    deprecated = False
                # remove c++ style comments
                lines1 = re.sub(pattern, replacer, lines1)
                lines2 = re.sub(pattern, replacer, lines2)
                # split in lines
                lines1 = lines1.splitlines()
                lines2 = lines2.splitlines()
                # remove spaces and tabs
                lines1 = sorted(map(lambda s: s.strip().replace(" ",""), lines1))
                lines2 = sorted(map(lambda s: s.strip().replace(" ",""), lines2))
                # removing empty lines
                lines1 = [line for line in lines1 if line.strip()]
                lines2 = [line for line in lines2 if line.strip()]

                n_diff_lines = 0
                for lineA in lines1:
                    found = False
                    most_similar = ''
                    max_ratio = 0
                    for lineB in lines2:
                        ratio = SequenceMatcher(None, lineA, lineB).ratio()
                        if ratio == 1.0:
                            lines2.remove(lineB)
                            found = True
                            break
                        elif ratio > max_ratio and ratio > 0.5:
                            most_similar = lineB
                            max_ratio = ratio

                    if not found:
                        n_diff_lines +=1
                        diff_lines.append([lineA, most_similar])
        return n_diff_lines, diff_lines, deprecated


    def grep_ice_compare(self, first_file, second_file, output_dir):
        """
        TODO: Deprecated.
        Execute cmake on the curren directory . Output and error is saved to make_output.log.
        :return: command return code
        """
        second_file_name = os.path.splitext(os.path.basename(second_file))[0]
        log_file = os.path.join(output_dir, second_file_name+"_comparison.log")
        with open(log_file, "wb") as log:
            command_output = subprocess.Popen("grep -Fxv -f %s %s" % (first_file, second_file),
                                              stdout=log,
                                              stderr=log,
                                              shell=True)
            stdout, stderr = command_output.communicate()
            # print(stdout)
            # print(stderr)
        diff_lines = -1
        deprecated = True
        with open(log_file, "r") as log:
            for log_lines, l in enumerate(log):
                if "Generated by RoboCompDSL" in l:
                    deprecated = False

        return diff_lines, deprecated


    def remove_genetared_files(self, current_dir, dry_run=True):
        """
        Remove all the .log and .ice files from the given dir.
        :param current_dir: Directory to look for files to remove.
        :param dry_run: Just show the output. No rm is really executed.
        :return: None
        """
        if os.path.isdir(current_dir):
            component_files = os.listdir(current_dir)
            # Remove not useful files
            remove_dir = True
            for next_file in component_files:
                if next_file.endswith(".ice") or next_file.endswith(".log"):
                    if dry_run:
                        print("rm -r %s" % next_file)
                    else:
                        full_path_ice = os.path.join(current_dir, next_file)
                        if os.path.isfile(full_path_ice):
                            os.remove(full_path_ice)
                        else:
                            rmtree(full_path_ice)
                else:
                    remove_dir = False
            if remove_dir:
                if dry_run:
                    print("rm -r %s" % current_dir)
                else:
                    rmtree(current_dir)

    def check_ice_generation(self, idsls_dir, dry_run, dirty, output_dir=".", generate_only=False, filter="", visual=False):
        """
        Main method of the class. Generate needed code, compile and show the results
        :param idsls_dir: alternative dir for the idsl files
        :param dry_run: just show what would be done. No file is removed.
        :param dirty: Leave all the generated files. No clean is done at the end of the script.
        :param generate_only: No compilation is executed for the components.
        :param filter: A string can be given to filter the directory of the components to be generated/compiled.
        :param clean_only: Just clean the generated files.
        :return: None
        """
        output_dir = os.path.join(output_dir, "auto_generated_ice_files")
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)
        self.dry_run = dry_run
        previous_dir = os.getcwd()
        list_dir = os.listdir(idsls_dir)
        for file in list_dir:
            if file.endswith(".idsl") and filter in file:
                idsl_file = file
                idsl_path = os.path.join(idsls_dir,idsl_file)
                self.valid += 1
                self.results[idsl_path] = {'generation': False, 'comparation': False }
                code, ice_path = self.generate_code(idsl_path, output_dir, self.dry_run)
                if code == 0:
                    console.print("%s generation OK" % ice_path, style='green')
                    self.results[idsl_path]['new_ice_path'] = ice_path
                    self.results[idsl_path]['generation'] = True
                    self.generated += 1
                    if generate_only:
                        self.results[idsl_path]['comparation'] = False
                        print("%s not compared (-g option)" % file)
                        self.comp_failed +=1
                    else:
                        print("Executing comparation for %s ... WAIT!" % (ice_path))
                        original_ice_file = os.path.join(idsls_dir, "..", os.path.basename(ice_path))
                        self.results[idsl_path]['original_ice_path'] = original_ice_file
                        self.results[idsl_path]['diff_lines'] = []
                        if os.path.isfile(original_ice_file):
                            n_diff_lines, diff_lines, deprecated = self.statistical_ice_file_comparation(original_ice_file, ice_path)
                            self.results[idsl_path]['diff_lines'] = diff_lines
                            self.results[idsl_path]['n_diff_lines'] = n_diff_lines
                            self.results[idsl_path]['deprecated'] = deprecated
                        else:
                            self.results[idsl_path]['n_diff_lines'] = -1
                            self.results[idsl_path]['deprecated'] = deprecated

                        if n_diff_lines == 0 or self.dry_run:
                            self.results[idsl_path]['comparation'] = True
                            self.compared += 1
                            console.print("%s comparation OK" % idsl_path, style='green')
                        else:
                            self.results[idsl_path]['comparation'] = False
                            self.comp_failed += 1
                            console.print("%s comparation FAILED" % idsl_path, 'red')


                else:
                    console.print("%s generation FAILED"%idsl_path, 'red')
                    self.gen_failed += 1
                    self.results[idsl_path]['generation'] = False

        # Command final output
        print("%d idsl files found" % self.valid)
        print("%d ice files generated OK (%d failed)" % (self.generated, self.gen_failed))
        print("%d are identical (%d are different)" % (self.compared, self.comp_failed))

        for file, result in self.results.items():
            cname = Text(result['new_ice_path'], 'magenta')

            # Printing results for generation
            if result['generation']:
                gen_result = Text("TRUE", style='green')
            else:
                gen_result = Text("FALSE", 'red')

            # Printing results for compilation
            if result['comparation']:
                comp_result = Text("TRUE", style='green')
            else:
                comp_result = Text("FALSE", 'red')

            if generate_only:
                print("\t%s have been generated? %s" % (cname, gen_result))
            else:
                print("\t%s have been generated? %s Are equal? %s %s different lines" % (cname, gen_result, comp_result, result['n_diff_lines']), end='')
                if result['deprecated']:
                    console.print("*", "magenta", attrs=['bold'])
                else:
                    print('')



            if visual and not result['comparation'] and result['generation']:
                print("\t\tOLD <-> NEW")
                for lines in result['diff_lines']:
                    print("\t\t%s <-> %s"%tuple(lines))
                # with open("meld.log", "wb") as log:
                #     command_output = subprocess.Popen("meld %s %s"%(result['original_ice_path'], result['new_ice_path']),
                #                                       stdout=log,
                #                                       stderr=log,
                #                                       shell=True)
                #
                #     stdout, stderr = command_output.communicate()

        if not dirty:
            self.remove_genetared_files(output_dir, self.dry_run)
        print("")
        os.chdir(previous_dir)
        console.print("The * indictate that the old file is probably deprecated and generated with an old version of .ice generation.", "magenta", attrs=['bold'])


if __name__ == '__main__':
    parser = MyParser(description=Text(
        'This application generate .ice files from idsl files to check generation and comparation  to old verions  \n', 'magenta'),
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('indir', type=str, help='Input dir for idsl files')
    parser.add_argument('outdir', nargs='?', default=os.getcwd(), help='Output dir for .ice and .log files')
    parser.add_argument("-g", "--generate-only", action="store_true",
                        help="Only the generation with robocompdsl is checked. No comparation is checked.")
    parser.add_argument("-d", "--dirty",
                        help="No cleaning is done after execution. All .ice and .log files will be left on the output dir.",
                        action="store_true")
    # parser.add_argument("-c", "--clean",
    #                     help="Just clean all source files and temp will be left on their dirs. .cdsl, .smdsl and .logs are kept on their dirs.",
    #                     action="store_true")
    parser.add_argument("-n", "--dry-run",
                        help="Executing dry run. No remove, generation or comparation will be executed in dry run mode.",
                        action="store_true")
    parser.add_argument("-i", "--installation", type=str,
                        help="Option to change where the robocompdsl.py tool script will be found.",
                        default="/opt/robocomp/tools/robocompdsl/")
    parser.add_argument("-f", "--filter", type=str,
                        help="Execute the checks only for .idsl files containing the FILTER string.", default="")
    parser.add_argument("-v", "--visual",
                        help="gives a visual output of the different lines at the end  of the execution for each file.",
                        action="store_true")
    args = parser.parse_args()

    outdir = os.path.abspath(args.outdir)
    if os.getcwd() != args.outdir:
        if not os.path.isdir(args.outdir):
            outdir = os.path.abspath(args.outdir)
            if not os.path.isdir(outdir):
                console.print("Output dir not found: %s" % args.outdir, 'red')
                exit(1)

    try:
        checker = ComponentGenerationChecker()
        checker.check_ice_generation(args.indir, args.dry_run, args.dirty, outdir, args.generate_only,
                                     args.filter, args.visual)
    except (KeyboardInterrupt, SystemExit):
        console.print("\nExiting in the middle of the execution.", 'red')
        console.print("Some files will be left on the directories.", 'yellow')
        console.print("Use -c option to clean all the generated files.", 'yellow')
        sys.exit()
    except Exception as e:
        console.print("Unexpected exception: %s"%e.message, 'red')
        traceback.print_exc()


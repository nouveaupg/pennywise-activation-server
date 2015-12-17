import hashlib
import sys
import json

USAGE = """Usage: python verify-code.py <file>
returns SHA256 of file or error if file could not be opened for reading (check your permissions)

python verify-code.py --sig-file <file>
verifies all the checksums of all files listed in the signature file"""

if __name__ == "__main__":
    if len(sys.argv) == 2:
        fo = file(sys.argv[1],"rb")
        if fo:
            file_data = fo.read()
            fo.close()
            m = hashlib.sha256()
            m.update(file_data)
            output = m.hexdigest()
            print "SHA256: " + output.upper()
        else:
            print "Could not open file for reading: " + sys.argv[1]
    elif len(sys.argv) == 3:
        if sys.argv[1] != "--sig-file":
            print USAGE
            sys.exit(1)

        fo = file(sys.argv[2],"rb")
        if fo:
            config_data = json.load(fo)
            fo.close()
            file_counter = 0
            verified_files = 0
            for each_file in config_data:
                file_counter += 1
                version_data = config_data[each_file]
                fo = file(each_file,"rb")
                if fo:
                    file_data = fo.read()
                    fo.close()
                    m = hashlib.sha256()
                    m.update(file_data)
                    md = m.hexdigest().upper()
                    version_found = None
                    for each_version in version_data:
                        if md == version_data[each_version]:
                            version_found = each_version
                            verified_files += 1
                            break
                    if version_found:
                        print "%s: VERIFIED (version %s)" % (each_file,version_found)
                    else:
                        print "%s: *** INVALID SIGNATURE *** WARNING! FILE SIGNATURE DOESN'T MATCH ANY OFFICIAL VERSION"
                else:
                    print each_file + ": File couldn't be opened for reading (check permissions)."
            print "\n%d out of %d file(s) verified.\n" % (verified_files,file_counter)
            if verified_files < file_counter:
                print "WARNING! Not all files were verified. Make certain they have not been tampered with.\n"
        else:
            print "Could not open signature file for reading (check permissions): " + sys.argv[1]
    else:
        print USAGE

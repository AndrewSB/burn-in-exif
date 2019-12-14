import os

'''
    From https://thispointer.com/python-how-to-get-list-of-files-in-directory-and-sub-directories/
    For the given path, get the List of all files in the directory tree 
'''
def getListOfFiles(dirName):
    # create a list of file and sub directories 
    # names in the given directory 
    listOfFile = os.listdir(dirName)
    allFiles = list()
    # Iterate over all the entries
    for entry in listOfFile:
        # Create full path
        fullPath = os.path.join(dirName, entry)
        # If entry is a directory then get the list of files in this directory 
        if os.path.isdir(fullPath):
            allFiles = allFiles + getListOfFiles(fullPath)
        else:
            allFiles.append(fullPath)
                
    return allFiles      

def safe_list_subscript(list, idx, default=None):
    try:
        return list[idx]
    except IndexError:
        return default

# a/b/c/d => c
def parent_dir_name(file_path):
    print('NYI')
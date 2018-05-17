#
# Imports
#
import requests
import shutil
import re
import os.path as path

from IPython.display import Markdown, display

def print_registry_row(row):
    """
    Pretty print registry result row.
    
    Parameters
    ----------
    row : astropy.table.Row
        This astropy Table row is expected to come from a registry query result.
    
    Returns
    -------
    None
    """
    md = '### {} ({})'.format(row['short_name'], row['ivoid'])
    display(Markdown(md))
    print(row['res_description'])
    print('More info: {}'.format(row['reference_url']))
    print('Access URL: {}'.format(row['access_url']))  
    
def download_file(url, directory=None, filename=None, verbose=False):
    """
    Download a file from the specified URL, making a best guess at the 
    output file name when no file name specified.  The logic works as
    follows:
    
       - If filename is specified, then that filename is used.
       - If filename is not specified, but the http response 
         from the URL has a content-disposition that suggests
         a filename, then use that.
       - If filename still isn't know, extract the base filename
         from the URL and use that.
         
    Parameters
    ----------
    url : str
        This URL from which to retrieve the file.
    directory : str
        The directory to which to write the file.  If not specified,
        the file will be written to the current working directory.
        May not be specified if filename contains a directory path.
    filename : str
        The filename to which to write the file.  When specified, 
        the file will be written to that name.  filename may contain
        a directory path only if the directory param is not specified.
    
    Returns
    -------
    str 
        The output path to which the file was written.
    """
    # Ensure that directory wasn't specified in both params.
    if filename is not None:
        dirname = path.dirname(filename)
        if directory is not None and dirname is not '':
            raise ValueError('directory cannot be specified if filename contains a dirname.')
                    
    #Send a request for this file.
    response = requests.get(url, stream=True)
    
    # See if the response header suggests a filename.
    cd = response.headers.get('content-disposition', '')
    re_results = re.findall("filename=(.+)", cd)
    cd_fname = None
    if len(re_results) > 0:
        cd_fname = re_results[0].replace('"', '')

    #Remove the path from the URL to isolate the name we should output to file.
    url_basename = path.basename(url)
    
    # Compute base_filename, using the parameter value if it exists.
    base_filename = filename
    if base_filename is None:
        if cd_fname is not None:
            base_filename = cd_fname
        else:
            base_filename = url_basename
    
    # Compute the full path.
    out_path = base_filename
    if directory is not None:
        out_path = path.join(directory, base_filename)

    # Verbose output
    if verbose:
        print(f'''
download() verbose output:
    filename param: {filename}
    content-disposition filename: {cd_fname}
    filename from URL: {url_basename}
    computed base_filename: {base_filename}
    computed full out_path: {out_path}
        ''')
        
    # Write out the file.
    with open(out_path, 'wb') as out_file:
        shutil.copyfileobj(response.raw, out_file)
        
    return out_path

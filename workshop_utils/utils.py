#
# Imports
#
from IPython.display import Markdown, display

#
# Pretty print registry result row
#
def print_registry_row(row):
    md = '### {} ({})'.format(row['short_name'], row['ivoid'])
    display(Markdown(md))
    print(row['res_description'])
    print('More info: {}'.format(row['reference_url']))
    print('Access URL: {}'.format(row['access_url']))  
    
   
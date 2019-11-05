import json
from iSkyLIMS_core.models import Samples, MoleculePreparation, Protocols
from iSkyLIMS_core.utils.handling_commercial_kits import *
from iSkyLIMS_wetlab.models import *
from iSkyLIMS_wetlab.wetlab_config import *
from iSkyLIMS_wetlab.utils.sample_sheet_utils import *
from ..fusioncharts.fusioncharts import FusionCharts
from .stats_graphics import *



def analyze_input_param_values(request):
    if  'lib_prep_in_list' in request.POST:
        lib_prep_ids = request.POST.getlist('lib_prep_id')
        if len('lib_prep_in_list') == 0:
            lib_prep_ids = list(request.POST['lib_prep_id'])
    else:
        lib_prep_ids = request.POST['lib_prep_id'].split(',')
    headings = request.POST['heading_in_excel'].split(',')
    json_data = json.loads(request.POST['protocol_data'])
    fixed_heading_length = len(HEADING_FIX_FOR_ADDING_LIB_PARAMETERS)
    parameters_length = len(headings)
    stored_params = []
    for i in range(len(lib_prep_ids)):
        library_prep_obj = LibraryPreparation.objects.get(pk = lib_prep_ids[i])

        for p_index in range(fixed_heading_length, parameters_length):
            lib_parameter_value ={}
            lib_parameter_value['parameter_id'] = ProtocolParameters.objects.get(protocol_id = library_prep_obj.protocol_id,
                                parameterName__exact = headings[p_index])
            lib_parameter_value['library_id'] = library_prep_obj
            lib_parameter_value['parameterValue'] = json_data[i] [p_index]

            new_parameters_data = LibParameterValue.objects.create_library_parameter_value (lib_parameter_value)
        kit_index = HEADING_FIX_FOR_ADDING_LIB_PARAMETERS.index('Lot Regents Kit used')
        library_prep_obj.set_reagent_user_kit(json_data[i] [kit_index])
        stored_params.append([library_prep_obj.get_sample_name(), library_prep_obj.get_lib_prep_code()])
        library_prep_obj.set_state('Completed')
        sample_obj = library_prep_obj.get_sample_obj ()
        # Update the sample state to "Create Pool"
        sample_obj.set_state('Pool Preparation')
    #import pdb; pdb.set_trace()
    return stored_params


def extract_sample_data (s_data):
    headings = s_data['headings']
    sample_list = []
    #columns = ['Sample_ID','Sample_Name','Sample_Plate','Sample_Well','Index_Plate_Well','I7_Index_ID','index','I5_Index_ID','index2','Sample_Project']
    for sample_row in s_data['samples']:
        '''
        if Samples.objects.filter(sampleName__exact = sample_row.index('Sample_Name'), sampleState__sampleStateName = 'Add Library Preparation' ).exists():
            sample_obj = Samples.objects.filter(sampleName__exact = sample_row.index('Sample_Name'), sampleState__sampleStateName = 'Add Library Preparation')
        '''
        lib_prep_data = {}
        for column in wetlab_config.MAP_USER_SAMPLE_SHEET_TO_DATABASE :
            if column[0] in headings:
                lib_prep_data[column[1]] = sample_row[headings.index(column[0])]
            else:
                lib_prep_data[column[1]] = ''
        sample_list.append(lib_prep_data)

    return sample_list

def find_duplicate_index (extracted_data):
    index_values = {}


    for sample_row in extracted_data:
        indexes_in_sample = str(sample_row['i7IndexID'] + '_' + sample_row['i5IndexID'])
        if  indexes_in_sample not in index_values:
            index_values[indexes_in_sample] = []
        index_values[indexes_in_sample].append(sample_row['sample_id'])

    if len(extracted_data) == len(index_values.keys()):
        return False
    else:
        incompatible_index = []

        for key, values in index_values.items():
            if len(values) > 1:
                incompatible_index.append([key, ' and  '.join(values)])
        return incompatible_index


def get_protocol_lib ():
    protocol_list = []
    if Protocols.objects.filter(type__protocol_type__exact ='Library Preparation').exists():
        protocols = Protocols.objects.filter(type__protocol_type__exact = 'Library Preparation')
        for protocol in protocols:
            protocol_list.append(protocol.get_name())
    return protocol_list


def get_all_library_information(sample_id):
    library_information = {}
    if LibraryPreparation.objects.filter(sample_id__pk__exact = sample_id).exists():
        library_information['library_definition_heading'] = HEADING_FOR_LIBRARY_PREPARATION_DEFINITION
        library_information['library_definition'] = []
        library_information['pool_information'] = []
        library_preparation_items = LibraryPreparation.objects.filter(sample_id__pk__exact = sample_id).exclude(libPrepState__libPrepState__exact = 'Created for Reuse')
        library_information['lib_prep_param_value'] = []
        for library_item in library_preparation_items:
            library_information['library_definition'].append(library_item.get_info_for_display())
            protocol_used_obj = library_item.get_protocol_obj()
            if ProtocolParameters.objects.filter(protocol_id = protocol_used_obj).exists():
                parameter_names = ProtocolParameters.objects.filter(protocol_id = protocol_used_obj).order_by('parameterOrder')
                lib_prep_param_heading = ['Lib Preparation CodeID']
                lib_prep_param_value = [library_item.get_lib_prep_code()]
                for p_name in parameter_names:
                    lib_prep_param_heading.append(p_name.get_parameter_name())
                    if LibParameterValue.objects.filter(library_id = library_item).exists():
                        import pdb; pdb.set_trace()
                        lib_prep_param_value.append(LibParameterValue.objects.get(library_id = library_item, parameter_id = p_name).get_parameter_information())
                library_information['lib_prep_param_value'].append(lib_prep_param_value)
                library_information['lib_prep_param_heading'] = lib_prep_param_heading

            if library_item.pools.all().exists() :
                pools = library_item.pools.all()
                lib_prep_code_id = library_item.get_lib_prep_code()
                for pool in pools:
                    pool_name = pool.get_pool_name()
                    pool_code = pool.get_pool_code_id()
                    library_information['pool_information'].append([lib_prep_code_id, pool_name,pool_code, ''])

        if library_information['pool_information']:
            library_information['pool_heading'] = HEADING_FOR_DISPLAY_POOL_INFORMATION_IN_SAMPLE_INFO
    return library_information

def get_lib_prep_to_add_parameters():
    '''
    Description:
        The function will return a list with samples which are needs to add library preparation parameters
    Input:

    Variables:
        library_prep_information # Dictionary with the heading and the molecule information
    Return:
        lib_prep_parameters.
    '''
    lib_prep_parameters = {}
    lib_prep_parameters['length'] = 0
    if LibraryPreparation.objects.filter(libPrepState__libPrepState__exact = 'Defined').exists():
        samples = LibraryPreparation.objects.filter(libPrepState__libPrepState__exact = 'Defined')
        sample_info = []
        for sample in samples:
            lib_prep_info = []
            lib_prep_info.append(sample.get_lib_prep_code())
            lib_prep_info.append(sample.get_sample_name())
            lib_prep_info.append(sample.get_protocol_used())
            lib_prep_info.append(sample.get_id())
            sample_info.append(lib_prep_info)
        lib_prep_parameters['lib_prep_info'] = sample_info
        lib_prep_parameters['lib_prep_heading'] = HEADING_FOR_ADD_LIBRARY_PREPARATION_PARAMETERS
        lib_prep_parameters['length'] = len(sample_info)
    return lib_prep_parameters



def check_samples_in_lib_prep_state ():
    '''
    Description:
        The function will return a list with samples which are in add_library_preparation state.
        Include the ones that are requested to reprocess
    Return:
        sample_names.
    '''

    sample_names = []

    if Samples.objects.filter(sampleState__sampleStateName__exact = 'Library preparation').exists():
        samples_obj = Samples.objects.filter(sampleState__sampleStateName__exact =  'Library preparation')

        for sample in samples_obj :
            if not LibraryPreparation.objects.filter(sample_id = sample).exists():
                sample_names.append(sample.get_sample_name())
                continue
            if LibraryPreparation.objects.filter(sample_id = sample, libPrepState__libPrepState__exact = 'Defined').exists():
                continue
            else:
                sample_names.append(sample.get_sample_name())
            '''
            if LibraryPreparation.objects.filter(sample_id = sample, libPrepState__libPrepState__exact = 'Created for Reuse').exists():
                sample_names.append(sample.get_sample_name())
            '''

    return sample_names

    #if LibraryPreparation.objects.filter(libPrepState__libPrepState__exact = 'Defined').exists():
    #lib_preparations = libraryPreparation.objects.filter(libPrepState__libPrepState__exact = 'Defined')

def pending_samples_for_grafic(pending):
    number_of_pending = {}
    number_of_pending ['DEFINED'] = pending['defined']['length']
    number_of_pending ['EXTRACTED MOLECULE'] = pending['extract_molecule']['length']
    number_of_pending ['LIBRARY PREPARATION'] = len(pending['create_library_preparation'])

    data_source = graphic_3D_pie('Number of Pending Samples', '', '', '', 'fint',number_of_pending)
    graphic_pending_samples = FusionCharts("pie3d", "ex1" , "430", "450", "chart-1", "json", data_source)
    return graphic_pending_samples

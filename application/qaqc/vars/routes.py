"""
VARS-specific QA/QC endpoints

/qaqc/vars/checklist [GET, PATCH]
/qaqc/vars/check/<check> [GET]
/qaqc/vars/quick-check/<check> [GET]
"""

import threading

import requests
from flask import current_app, render_template, request, session

from . import vars_qaqc_bp
from .vars_qaqc_processor import VarsQaqcProcessor
from application.util.constants import TERM_NORMAL, TERM_RED


# qaqc checklist page for vars
@vars_qaqc_bp.get('/checklist')
def vars_qaqc_checklist():
    sequences = request.args.getlist('sequence')
    total_counts = {
        'annotations': 0,
        'individuals': 0,
        'true_localizations': 0,  # number of bounding box associations in dive
        'group_localizations': 0,  # number of annotations marked 'group: localization'
    }
    with requests.get(
            url=f'{current_app.config.get("DARC_REVIEW_URL")}/vars-qaqc-checklist/{"&".join(request.args.getlist("sequence"))}',
            headers=current_app.config.get('DARC_REVIEW_HEADERS'),
    ) as checklist_res:
        if checklist_res.status_code == 200:
            checklist = checklist_res.json()
        else:
            print('ERROR: Unable to get QAQC checklist from external review server')
            checklist = {}
    # get counts
    threads = []
    for sequence in sequences:
        thread = threading.Thread(
            target=get_sequence_counts,
            args=(sequence, total_counts, current_app.config.get('VARS_DIVE_QUERY_URL')),
        )
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()
    return render_template(
        'qaqc/vars/qaqc-checklist.html',
        annotation_count=total_counts['annotations'],
        individual_count=total_counts['individuals'],
        true_localization_count=total_counts['true_localizations'],
        group_localization_count=total_counts['group_localizations'],
        checklist=checklist,
        tab_title=sequences[0] if len(sequences) == 1 else f'{sequences[0]} - {sequences[-1].split(" ")[-1]}'
    )


def get_sequence_counts(sequence_name, total_counts, vars_dive_url):
    identity_references = set()
    sequence_annotations = 0
    sequence_individuals = 0
    sequence_true_localizations = 0
    sequence_group_localizations = 0
    res = requests.get(f'{vars_dive_url}/{sequence_name.replace(" ", "%20")}')
    if res.status_code != 200:
        print(f'{TERM_RED}Failed to fetch annotations for sequence {sequence_name}{TERM_NORMAL}')
    annotations = res.json()['annotations']
    sequence_annotations += len(annotations)
    for annotation in annotations:
        if len(annotation['concept']) == 0 or annotation['concept'][0].islower():
            # ignore non-taxonomic concepts
            continue
        if annotation.get('group') == 'localization':
            sequence_true_localizations += 1
            sequence_group_localizations += 1
            continue
        id_ref = None
        cat_abundance = None
        pop_quantity = None
        for association in annotation['associations']:
            if association['link_name'] == 'identity-reference':
                id_ref = association['link_value']
            elif association['link_name'] == 'categorical-abundance':
                cat_abundance = association['link_value']
            elif association['link_name'] == 'population-quantity':
                pop_quantity = association['link_value']
            elif association['link_name'] == 'bounding box':
                sequence_true_localizations += 1
        if id_ref:
            if id_ref in identity_references:
                continue
            else:
                identity_references.add(id_ref)
        if cat_abundance:
            match cat_abundance:
                case '11-20':
                    sequence_individuals += 15
                case '21-50':
                    sequence_individuals += 35
                case '51-100':
                    sequence_individuals += 75
                case '\u003e100':
                    sequence_individuals += 100
            continue
        if pop_quantity and pop_quantity != '':
            sequence_individuals += int(pop_quantity)
            continue
        sequence_individuals += 1
    total_counts['annotations'] += sequence_annotations
    total_counts['individuals'] += sequence_individuals
    total_counts['true_localizations'] += sequence_true_localizations
    total_counts['group_localizations'] += sequence_group_localizations


# update vars qaqc checklist
@vars_qaqc_bp.patch('/checklist')
def patch_vars_qaqc_checklist():
    req_json = request.json
    sequences = req_json.get('sequences')
    if not sequences:
        return {}, 400
    req_json.pop('sequences')
    res = requests.patch(
        url=f'{current_app.config.get("DARC_REVIEW_URL")}/vars-qaqc-checklist/{sequences}',
        headers=current_app.config.get('DARC_REVIEW_HEADERS'),
        json=req_json,
    )
    return res.json(), res.status_code


# individual qaqc checks (VARS)
@vars_qaqc_bp.get('/check/<check>')
def vars_qaqc(check):
    sequences = request.args.getlist('sequence')
    qaqc_annos = VarsQaqcProcessor(
        sequence_names=sequences,
        vars_dive_url=current_app.config.get('VARS_DIVE_QUERY_URL'),
        vars_phylogeny_url=current_app.config.get('VARS_PHYLOGENY_URL'),
    )
    tab_title = sequences[0] if len(sequences) == 1 else f'{sequences[0]} - {sequences[-1].split(" ")[-1]}'
    data = {
        'concepts': session.get('vars_concepts', []),
        'title': check.replace('-', ' ').title(),
        'tab_title': f'{tab_title} {check.replace("-", " ").title()}',
    }
    match check:
        case 'multiple-associations':
            qaqc_annos.find_duplicate_associations()
            data['page_title'] = 'Records with multiples of the same association other than s2'
        case 'missing-primary-substrate':
            qaqc_annos.find_missing_s1()
            data['page_title'] = 'Records missing primary substrate'
        case 'identical-s1-&-s2':
            qaqc_annos.find_identical_s1_s2()
            data['page_title'] = 'Records with identical primary and secondary substrates'
        case 'duplicate-s2':
            qaqc_annos.find_duplicate_s2()
            data['page_title'] = 'Records with with duplicate secondary substrates'
        case 'missing-upon-substrate':
            qaqc_annos.find_missing_upon_substrate()
            data['page_title'] = 'Records missing a substrate that it is recorded "upon"'
        case 'mismatched-substrates':
            qaqc_annos.find_mismatched_substrates()
            data['page_title'] = 'Records occurring at the same timestamp with mismatched substrates'
        case 'missing-upon':
            qaqc_annos.find_missing_upon()
            data['page_title'] = 'Records other than "none" missing "upon"'
        case 'missing-ancillary-data':
            qaqc_annos.find_missing_ancillary_data()
            data['page_title'] = 'Records missing ancillary data'
        case 'id-ref-concept-name':
            qaqc_annos.find_id_refs_different_concept_name()
            data['page_title'] = 'Records with the same ID reference that have different concept names'
        case 'id-ref-associations':
            qaqc_annos.find_id_refs_conflicting_associations()
            data['page_title'] = 'Records with the same ID reference that have conflicting associations'
        case 'blank-associations':
            qaqc_annos.find_blank_associations()
            data['page_title'] = 'Records with blank association link values'
        case 'suspicious-hosts':
            qaqc_annos.find_suspicious_hosts()
            data['page_title'] = 'Records with suspicious hosts'
        case 'expected-associations':
            qaqc_annos.find_missing_expected_association()
            data['page_title'] = 'Records expected to be associated with an organism but "upon" is inanimate'
        case 'host-associate-time-diff':
            qaqc_annos.find_long_host_associate_time_diff()
            data['page_title'] = 'Records where "upon" occurred more than one minute ago or cannot be found'
        case 'localizations-missing-bounding-box':
            qaqc_annos.find_localizations_without_bounding_boxes()
            data['page_title'] = 'Records in the "localization" group that do not contain a "bounding box" association'
            data['page_subtitle'] = '(also displays records not in the "localization" group that contain a "bounding box" association)'
        case 'number-of-bounding-boxes':
            qaqc_annos.find_num_bounding_boxes()
            data['page_title'] = 'Number of bounding boxes for each unique concept'
            data['page_subtitle'] = ('Flags concepts with 0 boxes in red and >10 boxes in yellow. Also flags concepts with 1 box & only '
                                     '1 annotation in yellow')
        case 'unique-fields':
            qaqc_annos.find_unique_fields()
            data['unique_list'] = qaqc_annos.final_records
            return render_template('qaqc/vars/qaqc-unique.html', data=data)
    data['annotations'] = qaqc_annos.final_records
    return render_template('qaqc/vars/qaqc.html', data=data)


@vars_qaqc_bp.get('/quick-check/<check>')
def qaqc_quick(check):
    sequences = request.args.getlist('sequence')
    qaqc_annos = VarsQaqcProcessor(
        sequence_names=sequences,
        vars_dive_url=current_app.config.get('VARS_DIVE_QUERY_URL'),
        vars_phylogeny_url=current_app.config.get('VARS_PHYLOGENY_URL'),
    )
    match check:
        case 'missing-ancillary-data':
            records = qaqc_annos.get_num_records_missing_ancillary_data()
            return {'num_records': records}, 200
    return render_template('errors/404.html', err=''), 404

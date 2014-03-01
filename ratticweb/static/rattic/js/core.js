function genpassword() {
    var canset = [];
    var mustset = [];
    var passlength = parseInt($("#txt_length").val());

    for(var key in pass_settings) {
        if ($('#chk_must_' + key).is(":checked")) {
            mustset.push(key);
        }

        if ($('#chk_can_' + key).is(":checked")) {
            canset.push(key);
        }
    }

    $("input#id_password").val(make_password(passlength, canset, mustset));
}

function createTagModal(close) {
    ajax = RATTIC.api.createTag(
        $("input#tagname").val(),
        function(){
            $('#newtagmodal').modal('hide');
        },
        function(){
            if (ajax.status == 201 && close) {
                $('#newtagmodal').modal('hide');
                document.location.reload();
            }
            if (ajax.status == 201 && !close) {
                $('p#tagcreatedmessage').text($('input#tagname').val() + " has been created");
                $("input#tagname").val('');
            } 
        }
    );

    return false;
}

function submitCredForm(action) {
    if (countcheckboxes('.credcheck') == 0) return false;
    $('#credchecksubmitform')[0].action = action;
    $('#credchecksubmitform')[0].submit();
}

$(document).ready(function(){

    // Setup the Chosen select boxes
    $(".chzn-select").chosen();

    // Search boxes
    RATTIC.controls.searchForm($('.rattic-cred-search'));

    // Show password button on the edit screen
    RATTIC.controls.passShowButton($('button.btn-pass-show'));

    // Enable the password fetcher
    RATTIC.controls.passwordFetcher($('#password'), RATTIC.page.getCredId());

    // Setup checkboxes that check all values
    RATTIC.controls.checkAll($('input.rattic-checkall[type=checkbox]'));

    // Setup buttons that require one checked box to be enabled
    RATTIC.controls.checkEnabledButton($('.rattic-check-enabled'));

    // Add 'New Group' button next to group inputs if asked to
    if (RATTIC.page.getMetaInfo('attach_new_group_buttons') == 'true')
        RATTIC.controls.newGroupButton($('select#id_group'));

    // Add copy buttons to table cells
    RATTIC.controls.tableCopyButtons($('td.rattic-copy-button'));

});


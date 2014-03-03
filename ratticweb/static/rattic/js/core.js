$(document).ready(function(){
    // Setup the Chosen select boxes
    $(".chzn-select").chosen();

    // Start collecting random numbers
    sjcl.random.startCollectors();

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

    // Add functionality to the 'New Tag' buttons
    RATTIC.controls.newTagButton($('.rattic-new-tag'));

    // Add copy buttons to table cells
    RATTIC.controls.tableCopyButtons($('td.rattic-copy-button'));

    // Buttons that have an action set and submit a form
    RATTIC.controls.formSubmitButton($('button.rattic-form-submit'));

    // Add functionality to the password generator form
    RATTIC.controls.genPasswordModal($('.rattic-password-generator'));

    // Add functionality to clickable icons
    RATTIC.controls.clickableIcons($('.rattic-icon-clickable'));
});


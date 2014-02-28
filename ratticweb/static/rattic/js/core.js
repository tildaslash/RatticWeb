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

    // Fetch cred on details pages
    $('button.btn-pass-fetchcred').on('show', function() {
            target = $($(this).data('target'));
            cred_id = RATTIC.page.getCredId();
            RATTIC.api.getCred(cred_id, function(data) {
                target.text(data['password']);
            }, function(){});
        }
    );

    // Setup checkboxes that check all values
    RATTIC.controls.checkAll($('input.rattic-checkall[type=checkbox]'));

    // Setup buttons that require one checked box to be enabled
    RATTIC.controls.checkEnabledButton($('.rattic-check-enabled'));

    // Add 'New Group' button next to group inputs if asked to
    if (RATTIC.page.getMetaInfo('attach_new_group_buttons') == 'true')
        RATTIC.controls.newGroupButton($('select#id_group'));



    // Unconverted things
    clip = new ZeroClipboard()

    /* Mouse over the table cells */
    $('#usertd').on('mouseleave', function(){
        if (FlashDetect.installed) $('button#copyuser').css({visibility: 'hidden'})
    });

    $('#passtd').on('mouseleave', function(){
        if (FlashDetect.installed) $('button#copyclipboard').css({visibility: 'hidden'})
    });

    /* Mouse over the words themseves */
    $('#username').on('mouseover', function(){
        if (FlashDetect.installed) {
            $('button#copyuser').css({visibility: "visible"});
            clip.glue($('button#copyuser'));
        }
    });

    $('#password').on('mouseover', function(){
        RATTIC.api.getCred(RATTIC.page.getCredId(), function(data){
            if (FlashDetect.installed) {
                $('button#copyclipboard').css({visibility: "visible"})
                clip.glue($('button#copyclipboard'));
            }
            $('span#password').text(data['password']);
        }, function(){})
    });

    /* When we mouse over the button itself */
    clip.on('mouseover', function(client, args){
        if (FlashDetect.installed) {
            $('button#' + this.id).css({visibility: "visible"});
        }
    });

    /* When the copy button is clicked */
    clip.on( 'datarequested', function ( client, args ) {
        if (FlashDetect.installed) {
            switch (this.id) {
              case "copyclipboard":
                client.setText(RATTIC.api.getCredWait(RATTIC.page.getCredId())['password'])
                break;
              case "copyuser":
                client.setText($("span#username").text());
                break;
            }
        }
    } );

});


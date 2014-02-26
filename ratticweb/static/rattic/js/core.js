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

function credsearch(form) {
    var searchstr = form["box"].value
    if (searchstr.length > 0) window.location = url_root + "cred/list-by-search/" + searchstr + "/";
    return false;
}

function showpass(){
    if ( typeof showpass.password == 'undefined' ) {
        RATTIC.api.getCred(credId, function(data){
            showpass.password = data['password'];
            $('span#password').text(showpass.password);
            showpass();
        }, function(){});
    } else {
        $('span#password').removeClass('passhidden');
        $('a#showpass').css('display', 'none');
        $('a#hidepass').css('display', 'inline-block');
    }
}

function hidepass(){
    $('span#password').addClass('passhidden');
    $('a#showpass').css('display', 'inline-block');
    $('a#hidepass').css('display', 'none');
}

function togglepassinput(){
    input = $('input#id_password');
    button = $('button#passtoggle');
    if (input.attr('type') == 'password') {
        input.attr('type', 'text');
        button.html('<i class="icon-eye-close"></i>');
    } else {
        input.attr('type', 'password');
        button.html('<i class="icon-eye-open"></i>');
    }
}

function copycheckbox(allname, name){
    var checkval = $('input[name="' + allname + '"]').is(':checked');
    $('input[name="' + name + '"]').prop('checked', checkval);
}

function groupCreated(group) {
    $("select#id_group").append('<option value="' + group['id'] + '">' + group['name'] + '</option>');
    $("select#id_group").val(group['id']);
}

function createGroupModal() {
    ajax = RATTIC.api.createGroup(
        $("input#groupname").val(),
        function(){
            $('#addGroup').modal('hide');
            if (ajax.status == 201) groupCreated(JSON.parse(ajax.responseText))
        },
        function(){
            $('#addGroup').modal('hide');
        }
    );

    return false;
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

function countcheckboxes(parentclass) {
    return $(':checkbox:checked', parentclass).length
}

function updatebuttons() {
    if (countcheckboxes('.credcheck') > 0) {
        $('a.checkbutton').removeClass('disabled');
    } else {
        $('a.checkbutton').addClass('disabled');
    }
}

$(document).ready(function(){

    $(".chzn-select").chosen();

    if ((typeof attachstaffbuttons != 'undefined') && attachstaffbuttons) {
        $("select#id_group").after('<a href="#addGroup" role="button" class="btn" data-toggle="modal" data-loading-text="Adding...">Add</a>');

        $('#addGroup').on('show', function () {
            $("input#groupname").val('');
            $("button#saveGroupbutton").button('reset');
        });
    }

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
        RATTIC.api.getCred(credId, function(data){
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
                client.setText(RATTIC.api.getCredWait(credId)['password'])
                break;
              case "copyuser":
                client.setText($("span#username").text());
                break;
            }
        }
    } );

});


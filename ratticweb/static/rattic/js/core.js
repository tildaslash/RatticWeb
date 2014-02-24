function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

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
        getCred(credId, function(data){
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

function createGroup(name, successCallback, failureCallback) {
    return RATTIC.api.createGroup(name, successCallback, failureCallback);
}

function createTag(name, successCallback, failureCallback) {
    return RATTIC.api.createTag(name, successCallback, failureCallback);
}

function getCred(id, successcallback, failurecallback) {
    if ( typeof getCred.cred == 'undefined' ) {
        getCred.cred = [];
    }
    if ( typeof getCred.cred[id] == 'undefined' ) {
        $.ajax({
            url: url_root + 'api/v1/cred/' + id + '/',
            type: 'GET',
            contentType: 'application/json',
            beforeSend: function(jqXHR, settings) {
               jqXHR.setRequestHeader('X-CSRFToken', getCookie('csrftoken'));
            },
            success: function(data){
               getCred.cred[id] = data;
               successcallback(data);
            },
            error: failurecallback,
        })
    } else {
        successcallback(getCred.cred[id])
    }
}

function getCredWait(id) {
    if ( typeof getCred.cred == 'undefined' ) {
        getCred.cred = [];
    }
    if ( typeof getCred.cred[id] == 'undefined' ) {
        getCred.cred[id] = $.parseJSON($.ajax({
            url: url_root + 'api/v1/cred/' + id + '/',
            type: 'GET',
            contentType: 'application/json',
            beforeSend: function(jqXHR, settings) {
               jqXHR.setRequestHeader('X-CSRFToken', getCookie('csrftoken'));
            },
            async: false,
        }).responseText);
        return getCred.cred[id];
    } else {
        return getCred.cred[id]
    }
}

function groupCreated(group) {
    $("select#id_group").append('<option value="' + group['id'] + '">' + group['name'] + '</option>');
    $("select#id_group").val(group['id']);
}

function createGroupModal() {
    ajax = createGroup(
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
    ajax = createTag(
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
        getCred(credId, function(data){
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
                client.setText(getCredWait(credId)['password'])
                break;
              case "copyuser":
                client.setText($("span#username").text());
                break;
            }
        }
    } );

});


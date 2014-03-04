var RATTIC = (function ($, ZeroClipboard) {
    var my = {};
    my.api = {};
    my.controls = {};
    my.page = {};

    /********* Private Variables *********/
    var credCache = [];
    var rattic_meta_prefix = 'rattic_';
    var pass_settings = {
      "lcasealpha": {
        "description": "Lowercase Alphabet",
        "candefault": true,
        "mustdefault": false,
        "set": "abcdefghijklmnopqrstuvwxyz"
      },
      "ucasealpha": {
        "description": "Upper Alphabet",
        "candefault": true,
        "mustdefault": false,
        "set": "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
      },
      "numbers": {
        "description": "Numbers",
        "candefault": true,
        "mustdefault": false,
        "set": "0123456789"
      },
      "special": {
        "description": "Special",
        "candefault": false,
        "mustdefault": false,
        "set": "!@#$%^&*()_-+=:;\"',.<>?/\|"
      },
      "spaces": {
        "description": "Spaces",
        "candefault": false,
        "mustdefault": false,
        "set": " "
      }
    };

    /********* Page Methods **********/
    /* Get Meta information */
    my.page.getMetaInfo = function(name) {
        return $('head meta[name=' + rattic_meta_prefix + name + ']').attr('content');
    }

    /* Gets the cred for the page from the head */
    my.page.getCredId = function() {
        return my.page.getMetaInfo('cred_id');
    }

    /* Gets the the url root from the page */
    my.page.getURLRoot = function() {
        return my.page.getMetaInfo('url_root');
    }

    /* Setup ZeroClipboard */
    ZeroClipboard.config( { moviePath: my.page.getURLRoot() + 'static/zeroclipboard/1.3.2/ZeroClipboard.swf' } );

    /********* Private Methods **********/
    /* Gets a cookie from the browser. Only works for cookies that
     * are not set to httponly */
    function _getCookie(name) {
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

    /* Shortcut to get the CSRF cookie from django. Tastypie needs this to
     * perform session based authentication. */
    function _getCsrf() {
        return _getCookie('csrftoken');
    }

    /* Generic API call to Rattic. Handles the CSRF token and callbacks */
    function _apicall(object, method, data, success, failure) {
        if (method == 'GET') {
            url = my.page.getURLRoot() + 'api/v1/' + object + '/' + data + '/';
            data = undefined;
        } else {
            url = my.page.getURLRoot() + 'api/v1/' + object + '/';
        }

        return $.ajax({
            url: url,
            type: method,
            contentType: 'application/json',
            beforeSend: function(jqXHR, settings) {
                jqXHR.setRequestHeader('X-CSRFToken', _getCsrf())
            },
            data: data,
            success: success,
            failure: failure,
        })
    }

    function _apicallwait(object, method, data) {
        if (method == 'GET') {
            url = my.page.getURLRoot() + 'api/v1/' + object + '/' + data + '/';
            data = undefined;
        } else {
            url = my.page.getURLRoot() + 'api/v1/' + object + '/';
        }

        return $.parseJSON($.ajax({
            url: url,
            type: method,
            contentType: 'application/json',
            beforeSend: function(jqXHR, settings) {
                jqXHR.setRequestHeader('X-CSRFToken', _getCsrf())
            },
            data: data,
            async: false,
        }).responseText);
    };

    function _passShowButtonClick() {
        target = $($(this).data('target'));
        switch ($(this).data('status')) {
            case 'hidden':
                _passShowButtonShow($(this), target);
                break;
            case 'shown':
                _passShowButtonHide($(this), target);
                break;
        };
        return false;
    };

    function _passShowButtonShow(button, target) {
        target.trigger('getdata');
        button.trigger('show');
        button.data('status', 'shown');
        button.html('<i class="icon-eye-close"></i');
        target.removeClass('passhidden');
        if (target.prop('tagName') == 'INPUT') {
            target.attr('type', 'text');
        }
    };

    function _passShowButtonHide(button, target) {
        button.trigger('hide');
        button.data('status', 'hidden');
        button.html('<i class="icon-eye-open"></i');
        target.addClass('passhidden');
        if (target.prop('tagName') == 'INPUT') {
            target.attr('type', 'password');
        }
    };

    function _performCredSearch() {
        searchstr = $(this).children('input[type=search]').val();

        if (searchstr.length > 0)
            window.location = my.page.getURLRoot() + "cred/list-by-search/" + searchstr + "/";

        return false;
    };

    function _checkAllClick() {
        me = $(this);
        targets = $(me.data('target'));
        mystatus = me.is(':checked');
        targets.each(function() {
            me = $(this);
            if (me.prop('checked') != mystatus)
                me.trigger('click');
        });
    };

    function _countChecks(checkboxes) {
        return checkboxes.filter(':checked').length;
    };

    function _enableButtonHandler() {
        $.each($(this).data('linked'), function() {
            button = $(this);
            target = $(button.data('target'));
            if (_countChecks(target) > 0) {
                button.removeClass('disabled');
            } else {
                button.addClass('disabled');
            }
        });
    };

    function _createGroupFormClear() {
        $("input#groupname").val('');
        $("button#saveGroupbutton").button('reset');
    };

    function _groupCreated(group) {
        $("select#id_group").append(
                '<option value="' + group['id'] + '">' +
                group['name'] +
                '</option>');

        $("select#id_group").val(group['id']);
    };

    function _createGroupClick() {
        ajax = my.api.createGroup(
                $("input#groupname").val(),
                function(){
                    $('#addGroup').modal('hide');
                    if (ajax.status == 201) _groupCreated(JSON.parse(ajax.responseText))
                },
                function(){
                    $('#addGroup').modal('hide');
                });

        return false;
    };

    function _newTagClick() {
        me = $(this);
        input = $($(this).data('input'));
        inputval = input.val();
        message = $($(this).data('message'));
        ajax = RATTIC.api.createTag(
                inputval,
                function(){
                    if (ajax.status == 201) {
                        input.val('');
                        if (me.data('dismiss') == 'modal') {
                            document.location.reload();
                        } else {
                            message.text(inputval + ' has been created.')
                        }
                    }
                },
                function(){});
    };

    function _setVisibility(item, state) {
        if (state == true) state = 'visible';
        if (state == false) state = 'hidden';
        $(item).css({visibility: state});
    };

    function _hideCopyButton() {
        me = $(this);
        button = $($(me).data('copybutton'));
        hideTimeoutId = window.setTimeout(_hideCopyButtonTimer.bind(undefined, button), 250);
        button.data('hideTimeoutId', hideTimeoutId);
    };

    function _hideCopyButtonTimer(button) {
        _setVisibility(button, false);
        button.data('hideTimeoutId', -1);
    }

    function _showCopyButton() {
        button = $($(this).data('copybutton'));
        if (typeof button.data('hideTimeoutId') === "undefined")
            button.data('hideTimeoutId', -1);
        hideTimeoutId = button.data('hideTimeoutId');
        if (hideTimeoutId != -1) {
            window.clearTimeout(hideTimeoutId);
            button.data('hideTimeoutId', -1);
        }
        target = $(button.data('copyfrom'));
        clip = button.data('clip');
        target.trigger('getdatasync');
        _setVisibility(button, true);
        clip.glue(button);
    };

    function _copyButtonGetData(client) {
        me = $(this);
        target = $(me.data('copyfrom'));
        target.trigger('getdatasync');
        client.setText(target.text());
    };

    function _passfetcher() {
        me = $(this);
        cred_id = me.data('cred_id');
        my.api.getCred(cred_id, function(data) {
            me.text(data['password']);
        }, function(){});
    };

    function _passfetchersync() {
        me = $(this);
        cred_id = me.data('cred_id');
        me.text(my.api.getCredWait(cred_id)['password']);
    };

    function _formSubmitClick() {
        me = $(this);
        if (me.hasClass('disabled')) return false;

        form = me.parents('form:first');
        form.attr('action', me.data('action'));
        form.submit();
    };

    function _makePassword(length, can, must) {
        var pass = "";
        var canset = "";

        // get chars we must have    
        for (var x = 0; x < must.length; x++) {
            pass += _randomString(1, pass_settings[must[x]]['set']);
        }

        // get chars we can have    
        for (var x = 0; x < can.length; x++) {
            canset += pass_settings[can[x]]['set'];
        }

        // Make the rest of the password with 'can' chars
        pass += _randomString(length - pass.length, canset);

        // Shuffle the password
        pass = pass.split("");
        for (var x = 0; x < pass.length; x++) {
            var num = Math.abs(sjcl.random.randomWords(1)[0] % pass.length);
            var tmp = pass[num];
            pass[num] = pass[x];
            pass[x] = tmp;
        }

        return pass.join("");
    };

    function _randomString(length, sourcechars) {
        if (sourcechars.length == 0) return "";

        var charcount = sourcechars.length;
        var strout = "";

        for (var x = 0; x < length; x++) {
            var charnum = Math.abs(sjcl.random.randomWords(1)[0]) % charcount;
            strout += sourcechars[charnum];
        }

        return strout;
    };

    function _genPassClick() {
        me = $(this);
        input = $(me.data('input'));
        var canset = [];
        var mustset = [];
        var passlength = parseInt($("#txt_length").val());

        for(var key in pass_settings) {
            if ($('#chk_must_' + key).is(":checked")) mustset.push(key);
            if ($('#chk_can_' + key).is(":checked")) canset.push(key);
        }

        input.val(_makePassword(passlength, canset, mustset));
    };

    function _clickableIconClick() {
        me = $(this);
        iconname = me.data('icon-name');
        txtfield = $(me.data('txt-field'));
        imgfield = $(me.data('img-field'));

        txtfield.val(iconname);
        newtag = imgfield.clone();
        newtag.attr('class', me.attr('class'));
        newtag.removeClass('rattic-icon-clickable');
        imgfield.replaceWith(newtag);
    };

    /********* Public Variables *********/

    /********* Public Methods *********/
    /* Creates a Group */
    my.api.createGroup = function(name, success, failure) {
        var data = JSON.stringify({
            'name': name,
        });

        return _apicall('group', 'POST', data, success, failure);
    };

    /* Creates a Tag */
    my.api.createTag = function(name, success, failure) {
        var data = JSON.stringify({
            'name': name,
        });

        return _apicall('tag', 'POST', data, success, failure);
    };

    /* Gets a cred */
    my.api.getCred = function(id, success, failure) {
        if (typeof credCache[id] == 'undefined' ) {
            _apicall('cred',
                     'GET',
                     id,
                     function(data) {
                         credCache[id] = data;
                         success(data);
                     },
                     failure
                     );
        } else {
            success(credCache[id]);
        }
    };

    /* Gets a cred synchronous version */
    my.api.getCredWait = function(id) {
        if (typeof credCache[id] == 'undefined' ) {
            credCache[id] = _apicallwait('cred', 'GET', id);
            return credCache[id];
        } else {
            return credCache[id];
        }
    };

    /* Creates a password show and hide button */
    my.controls.passShowButton = function(buttons) {
        buttons.on('click', _passShowButtonClick);
        buttons.html('<i class="icon-eye-open"></i');
        buttons.data('status', 'hidden');
    }

    /* Creates a password show and hide button */
    my.controls.searchForm = function(form) {
        form.on('submit', _performCredSearch);
    }

    /* Creates a checkbox that controls other checkboxes */
    my.controls.checkAll = function(checkboxes) {
        checkboxes.on('click', _checkAllClick);
    }

    /* A button that is enabled when at least one box is checked */
    my.controls.checkEnabledButton = function(buttons) {
        buttons.each(function() {
            button = $(this);
            target = $($(this).data('target'));
            if (typeof target.data('linked') == "undefined") {
                target.data('linked', []);
                target.on('click', _enableButtonHandler);
            }
            target.data('linked').push(button);
        });
    };

    /* Adds a 'New Group' button to the group select box for staff */
    my.controls.newGroupButton = function(selectboxes) {
        selectboxes.after('<a href="#addGroup" role="button" class="btn" data-toggle="modal" data-loading-text="Adding...">New</a>');

        $('#addGroup').on('show', _createGroupFormClear);
        $('#saveGroupButton').on('click', _createGroupClick);
    };

    /* Adds functionality for the 'New Tag' button */
    my.controls.newTagButton = function(tagbuttons) {
        tagbuttons.on('click', _newTagClick);
    };

    /* Add copy buttons to table cells */
    my.controls.tableCopyButtons = function(cells) {
        if (!FlashDetect.installed) return false;

        cells.each(function() {
            // Get the players
            me = $(this);
            button = me.children('button');
            text = me.children('span');
            clip = new ZeroClipboard(button);

            // Set data for callbacks
            button.data('copyfrom', text);
            button.data('copybutton', button);
            button.data('clip', clip);
            me.data('copybutton', button);
            text.data('copybutton', button);

            // Apply callbacks
            me.on('mouseleave', _hideCopyButton);
            text.on('mouseover', _showCopyButton);
            clip.on('mouseover', _showCopyButton);
            clip.on('dataRequested', _copyButtonGetData);
        });

        return true;
    };

    /* Add data fetchers for the password spans */
    my.controls.passwordFetcher = function(fetcher, id) {
        fetcher.data('cred_id', id);
        fetcher.on('getdata', _passfetcher);
        fetcher.on('getdatasync', _passfetchersync);
    };

    /* Buttons that change a forms action, then submit it */
    my.controls.formSubmitButton = function(buttons) {
        buttons.on('click', _formSubmitClick);
    };

    /* Add functionality to the password generator form */
    my.controls.genPasswordModal = function(form) {
        button = $(form.data('button'));
        input = $(form.data('input'));
        button.data('form', form);
        button.data('input', input);
        button.on('click', _genPassClick);
    };

    /* Add functionality to the password generator form */
    my.controls.clickableIcons = function(icons) {
        icons.on('click', _clickableIconClick);
    };

    return my;
}(jQuery, ZeroClipboard));

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


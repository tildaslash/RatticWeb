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
  }
}

function make_password(length, can, must) {
    var pass = "";
    var canset = "";

    // get chars we must have    
    for (var x = 0; x < must.length; x++) {
        pass += randomstring(1, pass_settings[must[x]]['set']);
    }

    // get chars we can have    
    for (var x = 0; x < can.length; x++) {
        canset += pass_settings[can[x]]['set'];
    }

    // Make the rest of the password with 'can' chars
    pass += randomstring(length - pass.length, canset);

    // Shuffle the password
    pass = pass.split("");
    for (var x = 0; x < pass.length; x++) {
        var num = Math.abs(sjcl.random.randomWords(1)[0] % pass.length);
        var tmp = pass[num];
        pass[num] = pass[x];
        pass[x] = tmp;
    }

    return pass.join("");
}

function randomstring(length, sourcechars) {
    if (sourcechars.length == 0) return "";

    var charcount = sourcechars.length;
    var strout = "";

    for (var x = 0; x < length; x++) {
        var charnum = Math.abs(sjcl.random.randomWords(1)[0]) % charcount;
        strout += sourcechars[charnum];
    }

    return strout;
}


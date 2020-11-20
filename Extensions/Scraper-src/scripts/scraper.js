var COMMUNICATION_CODES = {
    "crawl":32860,
    "text":76456,
    "text sel":73452,
    "image":93726,
    "security":98500,
    "lookup":11173,
    "search":33967,
    "set afrun":3621
}

var SLEEP_TIME = 250;

// Not final
var IP = null;

function aux_get_ip(tab_id){
    browser.tabs.executeScript(
        tab_id,
        {
            code : "document.querySelector('scraperip').innerText;",
            matchAboutBlank : false
        }
    ).then(function (ip) {
        if(ip == ''){
            ip = false;
        } else {
            IP = ip;
        }
    }); 

    return IP;
}

function send(comm_code, send_data){
    var xhr = new window.XMLHttpRequest();

    xhr.open('post', 'http://'+IP, true);

    xhr.send(JSON.stringify({
        'command': comm_code,
        'data' : encodeURI(send_data)
    }));
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/menus/OnClickData
// https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/tabs/Tab
async function onclick_crawl(data, tab){
    //alert("Crawl ["+COMMUNICATION_CODES["crawl"]+"]");
    //alert(data.linkUrl || data.pageUrl);
    
    if(!IP){
        aux_get_ip(tab.id)

        while(IP === null) await sleep(SLEEP_TIME);
        
        if(!IP) return;
    }

    send( 
        COMMUNICATION_CODES["crawl"],
        data.linkUrl || data.pageUrl
    );
}

async function onclick_lookup(data, tab){
    //alert("Crawl ["+COMMUNICATION_CODES["crawl"]+"]");
    //alert(data.linkUrl || data.pageUrl);
    
    if(!IP){
        aux_get_ip(tab.id)

        while(IP === null) await sleep(SLEEP_TIME);
        
        if(!IP) return;
    }

    send( 
        COMMUNICATION_CODES["lookup"],
        data.linkUrl || ''
    );
}

async function onclick_text_analysis_selection(data, tab){
    // Had to do a separate function to skip one if
    // I also think this way is easier to read
    //alert("Text Analysis (selection) ["+COMMUNICATION_CODES["text sel"]+"]");
    //alert(data.selectionText);
    
    if(!IP){
        aux_get_ip(tab.id)

        while(IP === null) await sleep(SLEEP_TIME);
        
        if(!IP) return;
    }
    send( 
        COMMUNICATION_CODES["text sel"],
        data.selectionText
    );
}

async function onclick_text_analysis(data, tab){
    //alert("Text Analysis ["+COMMUNICATION_CODES["text"]+"]");
    //alert(data.linkUrl || data.pageUrl);
    
    if(!IP){
        aux_get_ip(tab.id)

        while(IP === null) await sleep(SLEEP_TIME);
        
        if(!IP) return;
    }

    send( 
        COMMUNICATION_CODES["text"],
        data.linkUrl || data.pageUrl
    );
}

async function onclick_image_analysis(data, tab){
    //alert("Image Analysis ["+COMMUNICATION_CODES["image"]+"]");
    //alert(data.srcUrl);
    
    if(!IP){
        aux_get_ip(tab.id)

        while(IP === null) await sleep(SLEEP_TIME);
        
        if(!IP) return;
    }

    send( 
        COMMUNICATION_CODES["image"],
        data.srcUrl
    );
}

async function onclick_security_check(data, tab){
    //alert("Security check ["+COMMUNICATION_CODES["security"]+"]");
    //alert(data.linkUrl);
    
    if(!IP){
        aux_get_ip(tab.id)

        while(IP === null) await sleep(SLEEP_TIME);
        
        if(!IP) return;
    }

    send( 
        COMMUNICATION_CODES["security"],
        data.linkUrl
    );
}

async function onclick_search(data, tab){
    //alert("Lookup ["+COMMUNICATION_CODES["search"]+"]");
    //alert(data.selectionText);

    if(!IP){
        aux_get_ip(tab.id)

        while(IP === null) await sleep(SLEEP_TIME);
        
        if(!IP) return;
    }

    send( 
        COMMUNICATION_CODES["set afrun"],
        data.selectionText
    );
}
    
async function onclick_run_after(data, tab){
    //alert("Lookup ["+COMMUNICATION_CODES["search"]+"]");
    //alert(data.selectionText);

    if(!IP){
        aux_get_ip(tab.id)

        while(IP === null) await sleep(SLEEP_TIME);
        
        if(!IP) return;
    }

    browser.tabs.executeScript(
        tab_id,
        {
        code : "window.scraper_run_after_msg;",
        matchAboutBlank : true
        }
    ).then(
            code_ => (
            send( 
                COMMUNICATION_CODES["search"],
                code_
            )
        )
    )
}

// ["all","audio","bookmark","browser_action","editable","frame","image","link","page","page_action","password","selection","tab","tools_menu","video"]

// Context menu creation
browser.menus.create({
    id: "test2",
    title: "Crawl",
    contexts: ["all"],
    onclick: onclick_crawl
});

browser.menus.create({
    id: "test10",
    title: "Lookup",
    contexts: ["all"],
    onclick: onclick_lookup
});


////

browser.menus.create({
    id: "separator1",
    type: "separator",
    contexts: ["all"]
});


browser.menus.create({
    id: "test3",
    title: "Selection Text Analysis",
    contexts: ["selection"],
    onclick: onclick_text_analysis_selection
});

browser.menus.create({
    id: "test3.1",
    title: "Website Text Analysis",
    contexts: ["browser_action","editable","frame","link","page","page_action","password", "selection"],
    onclick: onclick_text_analysis
});

browser.menus.create({
    id: "test4",
    title: "Image Analysis",
    contexts: ["image"],
    onclick: onclick_image_analysis
});

// Security check should *not* be a sub-menu
// setting it for debbugging purposes
browser.menus.create({
    id: "test5",
    title: "Security check",
    contexts: ["link"],
    onclick: onclick_security_check
});

////

browser.menus.create({
    id: "separator2",
    type: "separator",
    contexts: ["all"]
});

// General, Images, Videos, News, Shopping, Maps, Social, All
browser.menus.create({
    id: "test6",
    title: "Search",
    contexts: ["selection"],
    onclick: onclick_search
});

browser.menus.create({
    id: "separator3",
    type: "separator",
    contexts: ["all"]
});

browser.menus.create({
    id: "test7",
    title: "_set run after_",
    contexts: ["all"],
    onclick: onclick_run_after
});








//// TESTING

browser.windows.onCreated.addListener(themeWindow);

// Theme all currently open windows
browser.windows.getAll().then(wins => wins.forEach(themeWindow));

function themeWindow(window) {
  // Check if the window is in private browsing
  if (window.incognito) {
    browser.theme.update(window.id, {
      images: {
        theme_frame: "",
      },
      colors: {
        frame: "black",
        tab_background_text: "white",
        toolbar: "#333",
        bookmark_text: "white"
      }
    });
  }
}
browser.contextMenus.create({
  id: "malAnalysis",
  title: "MalAnalysis on AWS",
  contexts: ["all"]
});

browser.contextMenus.onClicked.addListener((info, tab) => {
  console.log(info.menuItemId)
  if (info.menuItemId === "malAnalysis") {
    const text = info.selectionText;
    const hashs = text.split(/\r\n|\n|\t/);
    console.log(hashs);

    let sendData = {
      hash: hashs
    }

    let json = JSON.stringify(sendData);
    console.log(json);
    // Set user API Gateway URL
    var url = "";
    doPost(url, json);
  }
});

function doPost(url, data) {
  console.log(url);
  var xhr = new XMLHttpRequest();
  xhr.open("POST", url);
  xhr.setRequestHeader("Content-Type", "application/json");
  xhr.onload = () => {
    console.log(xhr.responseText);
    console.log(xhr.status);
    console.log("success!");
    browser.tabs.create({
      url: xhr.responseText
    });
  };
  xhr.onerror = () => {
    console.log(xhr.status);
    console.log("error!");
  };
  xhr.send(data);
}

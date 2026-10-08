function isChincheta(window) {
    return String(window.resourceClass).toLowerCase() === "chincheta";
}

function updateKeepAbove(window) {
    if (isChincheta(window)) {
        window.keepAbove = /^Chincheta pinned [0-9]+$/.test(window.caption);
    }
}

function watchWindow(window) {
    if (!isChincheta(window)) {
        return;
    }
    updateKeepAbove(window);
    window.captionChanged.connect(function () {
        updateKeepAbove(window);
    });
}

if (workspace.windowList) {
    workspace.windowList().forEach(watchWindow);
    workspace.windowAdded.connect(watchWindow);
} else {
    workspace.clientList().forEach(watchWindow);
    workspace.clientAdded.connect(watchWindow);
}

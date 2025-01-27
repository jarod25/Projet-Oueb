import {places_emoji} from './emoji-files/emoji-places.js';
import {activities_emoji} from './emoji-files/emoji-activity.js';
import {flags_emoji} from './emoji-files/emoji-flags.js';
import {food_emoji} from './emoji-files/emoji-food.js';
import {nature_emoji} from './emoji-files/emoji-nature.js';
import {objects_emoji} from './emoji-files/emoji-objects.js';
import {people_emoji} from './emoji-files/emoji-people.js';
import {symbols_emoji} from './emoji-files/emoji-symbols.js';

$(document).ready(function () {
    const emojiButton = $(".emoji-btn");

    const emojiPopover = $("<div>").addClass("emoji-popover").css({
        position: "absolute",
        zIndex: 9999,
        maxHeight: "300px",
        maxWidth: "500px",
        overflow: "hidden",
        background: "#fff",
        border: "1px solid #ddd",
        borderRadius: "8px",
        display: "none",
    });

    const emojiCategories = {
        "😀": people_emoji,
        "🌳": nature_emoji,
        "🍔": food_emoji,
        "⚽": activities_emoji,
        "🗺️": places_emoji,
        "🛠️": objects_emoji,
        "💡": symbols_emoji,
        "🏳️‍🌈": flags_emoji,
    };

    const categoryList = $("<div>").css({
        display: "flex",
        flexDirection: "column",
        overflowY: "auto",
        maxHeight: "300px",
        gap: "5px",
        padding: "10px",
        borderRight: "1px solid #ddd",
        overflowX: "hidden",
    });

    const emojiContainer = $("<div>")
        .addClass("emoji-container")
        .css({
            display: "grid",
            gridTemplateColumns: "repeat(10, 1fr)",
            gap: "5px",
            overflowY: "auto",
            maxHeight: "300px",
            padding: "10px",
            flex: 1,
        });

    Object.keys(emojiCategories).forEach((category) => {
        const categoryButton = $("<button>")
            .addClass("emoji-category")
            .text(category)
            .css({
                fontSize: "24px",
                background: "transparent",
                border: "none",
                cursor: "pointer",
            })
            .on("click", () => scrollToCategory(category));
        categoryList.append(categoryButton);
    });

    emojiPopover.append(categoryList, emojiContainer);

    Object.entries(emojiCategories).forEach(([category, emojis], index) => {
        if (index > 0) {
            emojiContainer.append($("<hr>").css({
                gridColumn: "1 / -1",
                border: "none",
                borderTop: "1px solid #ddd",
                margin: "10px 0",
            }));
        }

        emojis.forEach((emoji) => {
            const emojiElement = $("<button>")
                .addClass("emoji-item")
                .text(emoji.character)
                .css({
                    fontSize: "24px",
                    border: "none",
                    background: "transparent",
                    cursor: "pointer",
                })
                .on("click", () => insertEmoji(emoji.character));
            emojiElement.attr("data-category", category);
            emojiContainer.append(emojiElement);
        });
    });

    function insertEmoji(emoji) {
        const textarea = $("#msg")[0];
        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        const text = textarea.value;

        textarea.value = text.substring(0, start) + emoji + text.substring(end);
        textarea.setSelectionRange(start + emoji.length, start + emoji.length);
        textarea.focus();
    }

    function scrollToCategory(category) {
        const firstEmoji = emojiContainer.find(`[data-category='${category}']`).first();
        if (firstEmoji.length) {
            emojiContainer.scrollTop(
                firstEmoji.position().top + emojiContainer.scrollTop() - emojiContainer.position().top
            );
        }
    }

    emojiContainer.on("scroll", function () {
        const scrollTop = $(this).scrollTop();
        let activeCategory = null;

        emojiContainer.find(".emoji-item").each(function () {
            if ($(this).position().top + scrollTop >= 0) {
                activeCategory = $(this).attr("data-category");
                return false;
            }
        });

        categoryList.find(".emoji-category").css("background", "transparent");
    });

    emojiButton.on("click", function (e) {
        console.log("emoji button clicked");
        e.stopPropagation();
        const rect = this.getBoundingClientRect();
        emojiPopover.css({
            top: rect.top + window.scrollY - emojiPopover.outerHeight() - 5,
            left: rect.left + window.scrollX,
            display: emojiPopover.css("display") === "none" ? "flex" : "none",
        });

        if (emojiPopover.css("display") === "flex") {
            emojiContainer.scrollTop(0);
        }
    });


    $(document).on("click", (e) => {
        if (!emojiPopover.is(e.target) && emojiPopover.has(e.target).length === 0 && !emojiButton.is(e.target)) {
            emojiPopover.hide();
        }
    });

    $("body").append(emojiPopover);
});

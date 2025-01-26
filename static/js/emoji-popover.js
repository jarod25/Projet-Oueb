import { places_emoji } from './emoji-files/emoji-places.js';
import { activities_emoji } from './emoji-files/emoji-activity.js';
import { flags_emoji } from './emoji-files/emoji-flags.js';
import { food_emoji } from './emoji-files/emoji-food.js';
import { nature_emoji } from './emoji-files/emoji-nature.js';
import { objects_emoji } from './emoji-files/emoji-objects.js';
import { people_emoji } from './emoji-files/emoji-people.js';
import { symbols_emoji } from './emoji-files/emoji-symbols.js';

import {getMessages, state} from "./ajax_room_messages.js";

$(document).ready(function () {
    const messagesContainer = $("#messages-container");
    const roomId = messagesContainer.data("room-id");

    // Fonction pour toujours scroller vers le bas
    function scrollToBottom() {
        messagesContainer.scrollTop(messagesContainer[0].scrollHeight);
    }

    // Activer/désactiver le bouton d'envoi en fonction de l'entrée
    $('#msg').on('input', function () {
        const sendButton = $('.send-btn');
        sendButton.prop('disabled', !$(this).val().trim().length);
    });

    // Gestion des emojis
    const emojiButton = document.querySelector('.emoji-btn');
    const emojiPopover = document.createElement('div');
    emojiPopover.classList.add('emoji-popover', 'popover', 'show');
    emojiPopover.style.position = 'absolute';
    emojiPopover.style.zIndex = 9999;
    emojiPopover.style.display = 'none';
    emojiPopover.style.maxHeight = '300px';
    emojiPopover.style.overflowY = 'auto';
    emojiPopover.style.background = '#fff';
    emojiPopover.style.border = '1px solid #ddd';
    emojiPopover.style.borderRadius = '8px';
    emojiPopover.style.padding = '10px';

    const emojiCategories = {
        Personnes: people_emoji,
        Nature: nature_emoji,
        Nourriture: food_emoji,
        Activités: activities_emoji,
        Endroits: places_emoji,
        Objets: objects_emoji,
        Symboles: symbols_emoji,
        Drapeaux: flags_emoji,
    };

    // Création des boutons de catégories
    const categoryBar = document.createElement('div');
    categoryBar.style.display = 'flex';
    categoryBar.style.justifyContent = 'space-around';
    categoryBar.style.marginBottom = '10px';

    Object.keys(emojiCategories).forEach(category => {
        const categoryButton = document.createElement('button');
        categoryButton.textContent = category;
        categoryButton.style.border = 'none';
        categoryButton.style.background = '#f8f9fa';
        categoryButton.style.padding = '5px 10px';
        categoryButton.style.cursor = 'pointer';
        categoryButton.style.borderRadius = '4px';
        categoryButton.addEventListener('click', () => loadEmojiCategory(category));
        categoryBar.appendChild(categoryButton);
    });

    emojiPopover.appendChild(categoryBar);

    // Conteneur pour les emojis
    const emojiContainer = document.createElement('div');
    emojiContainer.classList.add('emoji-container');
    emojiContainer.style.display = 'grid';
    emojiContainer.style.gridTemplateColumns = 'repeat(auto-fit, minmax(30px, 1fr))';
    emojiContainer.style.gap = '5px';
    emojiContainer.style.padding = '5px';
    emojiPopover.appendChild(emojiContainer);

    // Charger une catégorie d'emojis
    function loadEmojiCategory(category) {
        emojiContainer.innerHTML = '';
        const emojis = emojiCategories[category];
        emojis.forEach(emoji => {
            const emojiElement = document.createElement('button');
            emojiElement.classList.add('emoji-item');
            emojiElement.textContent = emoji.character;
            emojiElement.style.fontSize = '24px';
            emojiElement.style.border = 'none';
            emojiElement.style.background = 'transparent';
            emojiElement.style.cursor = 'pointer';
            emojiElement.addEventListener('click', () => insertEmoji(emoji.character));
            emojiContainer.appendChild(emojiElement);
        });
    }

    // Insérer l'emoji dans le champ d'entrée
    function insertEmoji(emoji) {
        const textarea = document.getElementById('msg');
        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        const text = textarea.value;

        textarea.value = text.substring(0, start) + emoji + text.substring(end);
        textarea.setSelectionRange(start + emoji.length, start + emoji.length);
        textarea.focus();
    }

    emojiButton.addEventListener('click', (e) => {
        e.stopPropagation();
        const rect = emojiButton.getBoundingClientRect();
        const popoverHeight = emojiPopover.offsetHeight || 300;
        emojiPopover.style.top = `${rect.top + window.scrollY - popoverHeight}px`; // Position au-dessus
        emojiPopover.style.left = `${rect.left + window.scrollX}px`;
        emojiPopover.style.display = emojiPopover.style.display === 'none' ? 'block' : 'none';
    });

    // Close popover on outside click
    document.addEventListener('click', (e) => {
        if (!emojiPopover.contains(e.target) && e.target !== emojiButton) {
            emojiPopover.style.display = 'none';
        }
    });

    // Charger la catégorie par défaut
    loadEmojiCategory('Personnes');

    // Ajouter le popover au DOM
    document.body.appendChild(emojiPopover);

    

    // Récupération initiale des messages
    getMessages();
    scrollToBottom();
});


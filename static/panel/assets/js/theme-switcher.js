/**
 * SISTEMA GROOMING - Theme Switcher
 * ==================================
 *
 * Script para cambiar dinamicamente entre temas.
 *
 * TEMAS DISPONIBLES:
 * - theme-orange: Tema naranja original (#e6603a)
 * - theme-navy: Tema azul oscuro (#13304D)
 *
 * USO:
 * - ThemeSwitcher.setTheme('theme-navy')  // Cambiar a tema navy
 * - ThemeSwitcher.setTheme('theme-orange') // Cambiar a tema naranja
 * - ThemeSwitcher.toggleTheme()            // Alternar entre temas
 * - ThemeSwitcher.getCurrentTheme()        // Obtener tema actual
 */

var ThemeSwitcher = (function() {

    // Configuracion de temas disponibles
    var themes = {
        'theme-orange': {
            name: 'Naranja',
            primary: '#e6603a',
            primaryDark: '#d55532',
            primaryLight: '#f08a6a',
            primaryLighter: '#fff8f6',
            primaryRgb: '230, 96, 58'
        },
        'theme-navy': {
            name: 'Navy',
            primary: '#13304D',
            primaryDark: '#0d2339',
            primaryLight: '#1a4166',
            primaryLighter: '#e8eef4',
            primaryRgb: '19, 48, 77'
        }
    };

    // Tema por defecto
    var defaultTheme = 'theme-navy';

    // Clave para localStorage
    var storageKey = 'grooming-theme';

    /**
     * Obtiene el tema guardado en localStorage o el tema por defecto
     */
    function getSavedTheme() {
        try {
            return localStorage.getItem(storageKey) || defaultTheme;
        } catch (e) {
            return defaultTheme;
        }
    }

    /**
     * Guarda el tema en localStorage
     */
    function saveTheme(themeName) {
        try {
            localStorage.setItem(storageKey, themeName);
        } catch (e) {
            console.warn('No se pudo guardar el tema en localStorage');
        }
    }

    /**
     * Aplica las variables CSS del tema seleccionado
     */
    function applyThemeVariables(themeName) {
        var theme = themes[themeName];
        if (!theme) {
            console.warn('Tema no encontrado:', themeName);
            return;
        }

        var root = document.documentElement;

        // Actualizar variables CSS personalizadas del tema
        root.style.setProperty('--theme-primary', theme.primary);
        root.style.setProperty('--theme-primary-dark', theme.primaryDark);
        root.style.setProperty('--theme-primary-light', theme.primaryLight);
        root.style.setProperty('--theme-primary-lighter', theme.primaryLighter);
        root.style.setProperty('--theme-primary-rgb', theme.primaryRgb);

        // Actualizar gradiente
        root.style.setProperty('--theme-gradient',
            'linear-gradient(135deg, ' + theme.primary + ' 0%, ' + theme.primaryDark + ' 100%)');
        root.style.setProperty('--theme-gradient-reverse',
            'linear-gradient(135deg, ' + theme.primaryDark + ' 0%, ' + theme.primary + ' 100%)');
        root.style.setProperty('--theme-gradient-light',
            'linear-gradient(135deg, ' + theme.primaryLight + ' 0%, ' + theme.primary + ' 100%)');
    }

    /**
     * Cambia el tema del sistema
     */
    function setTheme(themeName) {
        if (!themes[themeName]) {
            console.warn('Tema no valido:', themeName, '- Temas disponibles:', Object.keys(themes));
            return false;
        }

        // Cambiar el atributo data-theme del body
        document.body.setAttribute('data-theme', themeName);

        // Aplicar variables CSS
        applyThemeVariables(themeName);

        // Guardar en localStorage
        saveTheme(themeName);

        // Disparar evento personalizado para notificar el cambio
        var event = new CustomEvent('themeChanged', {
            detail: { theme: themeName, config: themes[themeName] }
        });
        document.dispatchEvent(event);

        console.log('Tema cambiado a:', themeName);
        return true;
    }

    /**
     * Alterna entre los temas disponibles
     */
    function toggleTheme() {
        var currentTheme = getCurrentTheme();
        var themeKeys = Object.keys(themes);
        var currentIndex = themeKeys.indexOf(currentTheme);
        var nextIndex = (currentIndex + 1) % themeKeys.length;
        setTheme(themeKeys[nextIndex]);
    }

    /**
     * Obtiene el tema actual
     */
    function getCurrentTheme() {
        return document.body.getAttribute('data-theme') || getSavedTheme();
    }

    /**
     * Obtiene la configuracion del tema actual
     */
    function getThemeConfig(themeName) {
        themeName = themeName || getCurrentTheme();
        return themes[themeName] || null;
    }

    /**
     * Obtiene el color primario del tema actual (util para SweetAlert2, etc.)
     */
    function getPrimaryColor() {
        var theme = getThemeConfig();
        return theme ? theme.primary : '#13304D';
    }

    /**
     * Inicializa el tema al cargar la pagina
     */
    function init() {
        var savedTheme = getSavedTheme();
        var currentBodyTheme = document.body.getAttribute('data-theme');

        // Si hay un tema guardado diferente al del body, aplicarlo
        if (savedTheme && savedTheme !== currentBodyTheme) {
            setTheme(savedTheme);
        } else if (currentBodyTheme) {
            // Aplicar variables del tema actual
            applyThemeVariables(currentBodyTheme);
        }
    }

    /**
     * Crea un boton de cambio de tema
     */
    function createThemeToggleButton(containerId) {
        var container = document.getElementById(containerId);
        if (!container) {
            console.warn('Contenedor no encontrado:', containerId);
            return null;
        }

        var button = document.createElement('button');
        button.type = 'button';
        button.className = 'btn btn-sm btn-outline-light theme-toggle-btn';
        button.innerHTML = '<i class="fa fa-paint-brush me-1"></i> Cambiar Tema';
        button.title = 'Alternar tema de colores';
        button.onclick = function() {
            toggleTheme();
            updateButtonText(button);
        };

        container.appendChild(button);
        updateButtonText(button);

        return button;
    }

    /**
     * Actualiza el texto del boton de tema
     */
    function updateButtonText(button) {
        var theme = getThemeConfig();
        if (theme && button) {
            button.innerHTML = '<i class="fa fa-paint-brush me-1"></i> Tema: ' + theme.name;
        }
    }

    // Inicializar cuando el DOM este listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // API publica
    return {
        setTheme: setTheme,
        toggleTheme: toggleTheme,
        getCurrentTheme: getCurrentTheme,
        getThemeConfig: getThemeConfig,
        getPrimaryColor: getPrimaryColor,
        createThemeToggleButton: createThemeToggleButton,
        themes: themes
    };

})();

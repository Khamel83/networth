(function () {
    'use strict';

    const NAV_LINKS = [
        { key: 'how-it-works', href: '/#how-it-works' },
        { key: 'courts', href: '/#courts' },
        { key: 'rules', href: '/rules' },
        { key: 'players', href: '/profiles', membersOnly: true },
        { key: 'rankings', href: '/#rankings', membersOnly: true },
    ];

    function readSession() {
        let player = {};
        try {
            player = JSON.parse(localStorage.getItem('networth_player') || '{}');
        } catch (_error) {
            player = {};
        }

        const token = localStorage.getItem('networth_token') || '';
        return { loggedIn: Boolean(player && player.email && token) };
    }

    function setVisibility(element, visible) {
        if (!element) return;
        element.hidden = !visible;
        element.setAttribute('aria-hidden', String(!visible));
    }

    function activePageKeys(page) {
        if (page === 'players' || page === 'profile') return new Set(['players']);
        if (page === 'rules') return new Set(['rules']);
        if (page === 'rankings') return new Set(['rankings']);
        return new Set();
    }

    function installNavigation() {
        const navRoot = document.querySelector('[data-site-nav]');
        if (!navRoot) return;

        const menu = navRoot.querySelector('[data-site-menu]');
        const toggle = navRoot.querySelector('[data-menu-toggle]');
        const page = document.body.dataset.page || '';
        const session = readSession();
        const activeKeys = activePageKeys(page);

        NAV_LINKS.forEach((definition) => {
            const link = navRoot.querySelector(`[data-nav-key="${definition.key}"]`);
            if (!link) return;

            if (definition.membersOnly) {
                setVisibility(link, session.loggedIn);
            }

            if (activeKeys.has(definition.key)) {
                link.setAttribute('aria-current', 'page');
                link.classList.add('is-active');
            } else {
                link.removeAttribute('aria-current');
                link.classList.remove('is-active');
            }
        });

        document.querySelectorAll('[data-members-only="true"]').forEach((element) => {
            if (!element.closest('[data-site-nav]')) {
                setVisibility(element, session.loggedIn);
            }
        });

        const signIn = navRoot.querySelector('[data-auth-action="signin"]');
        const join = navRoot.querySelector('[data-auth-action="join"]');
        const profile = navRoot.querySelector('[data-auth-action="profile"]');
        const signOut = navRoot.querySelector('[data-auth-action="signout"]');

        setVisibility(signIn, !session.loggedIn);
        setVisibility(join, !session.loggedIn);
        setVisibility(profile, session.loggedIn);
        setVisibility(signOut, session.loggedIn);

        function closeMenu({ restoreFocus = false } = {}) {
            if (!menu || !toggle) return;
            menu.classList.remove('is-open');
            toggle.setAttribute('aria-expanded', 'false');
            toggle.setAttribute('aria-label', 'Open navigation');
            if (restoreFocus) toggle.focus();
        }

        function openMenu() {
            if (!menu || !toggle) return;
            menu.classList.add('is-open');
            toggle.setAttribute('aria-expanded', 'true');
            toggle.setAttribute('aria-label', 'Close navigation');
        }

        if (menu && toggle) {
            toggle.addEventListener('click', () => {
                if (menu.classList.contains('is-open')) {
                    closeMenu();
                } else {
                    openMenu();
                }
            });

            document.addEventListener('keydown', (event) => {
                if (event.key === 'Escape' && menu.classList.contains('is-open')) {
                    closeMenu({ restoreFocus: true });
                }
            });

            document.addEventListener('pointerdown', (event) => {
                if (menu.classList.contains('is-open') && !navRoot.contains(event.target)) {
                    closeMenu();
                }
            });

            menu.querySelectorAll('a').forEach((link) => {
                link.addEventListener('click', () => closeMenu());
            });

            window.addEventListener('resize', () => {
                if (window.matchMedia('(min-width: 769px)').matches) closeMenu();
            });
        }

        if (signOut) {
            signOut.addEventListener('click', (event) => {
                event.preventDefault();
                localStorage.removeItem('networth_token');
                localStorage.removeItem('networth_refresh_token');
                localStorage.removeItem('networth_player');
                window.location.href = '/';
            });
        }

        window.NetWorthNav = { closeMenu };
        window.signOut = function signOutFromSharedNav() {
            signOut?.click();
        };
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', installNavigation);
    } else {
        installNavigation();
    }
})();

/**
 * app.js — Audio Metadata Manager (AMM) Web UI
 * Loaded globally via base.html. Provides:
 *   - Global search (top bar)
 *   - Global audio player
 *   - dashboardInit(), libraryInit(), editorInit(), settingsInit()
 *
 * Vanilla JS only — no frameworks.
 */

(function () {
    'use strict';

    /* ================================================================
       1. GLOBAL SEARCH — base.html #global-search
       ================================================================ */
    const globalSearch = document.getElementById('global-search');
    if (globalSearch) {
        globalSearch.addEventListener('keydown', function (e) {
            if (e.key === 'Enter') {
                const q = this.value.trim();
                if (q) {
                    window.location.href = '/library?q=' + encodeURIComponent(q);
                }
            }
        });
    }

    /* ================================================================
       2. GLOBAL AUDIO PLAYER
       ================================================================ */
    const _audio = new Audio();
    _audio.preload = 'metadata';
    let _isPlaying = false;

    const playerEl    = document.getElementById('audio-player');
    const playBtn     = document.getElementById('player-play');
    const filenameEl  = document.getElementById('player-filename');
    const timeEl      = document.getElementById('player-time');
    const volumeEl    = document.getElementById('player-volume');

    /**
     * playAudio(filePath, fileName)
     * Shows the bottom player bar and starts streaming /api/audio/{filePath}.
     */
    function playAudio(filePath, fileName) {
        if (!playerEl || !_audio) return;
        playerEl.classList.remove('hidden');
        if (filenameEl) filenameEl.textContent = fileName || filePath;

        _audio.src = '/api/audio/' + encodeURIComponent(filePath);
        _audio.play().then(function () {
            _isPlaying = true;
            _updatePlayIcon();
        }).catch(function (err) {
            if (filenameEl) filenameEl.textContent = '文件不可预览';
            if (timeEl) timeEl.textContent = '00:00 / 00:00';
            _isPlaying = false;
            _updatePlayIcon();
            console.warn('Audio play failed:', err);
        });
    }

    function _updatePlayIcon() {
        if (!playBtn) return;
        var icon = playBtn.querySelector('.material-symbols-outlined');
        if (icon) icon.textContent = _isPlaying ? 'pause' : 'play_arrow';
    }

    if (playBtn) {
        playBtn.addEventListener('click', function () {
            if (!_audio.src) return;
            if (_isPlaying) {
                _audio.pause();
                _isPlaying = false;
            } else {
                _audio.play().catch(function () {});
                _isPlaying = true;
            }
            _updatePlayIcon();
        });
    }

    // Time display
    function _formatTime(sec) {
        if (!isFinite(sec) || sec < 0) return '00:00';
        var m = Math.floor(sec / 60);
        var s = Math.floor(sec % 60);
        return (m < 10 ? '0' : '') + m + ':' + (s < 10 ? '0' : '') + s;
    }

    _audio.addEventListener('timeupdate', function () {
        if (timeEl) timeEl.textContent = _formatTime(_audio.currentTime) + ' / ' + _formatTime(_audio.duration);
    });

    _audio.addEventListener('loadedmetadata', function () {
        if (timeEl) timeEl.textContent = '00:00 / ' + _formatTime(_audio.duration);
    });

    _audio.addEventListener('ended', function () {
        _isPlaying = false;
        _updatePlayIcon();
    });

    _audio.addEventListener('error', function () {
        if (filenameEl) filenameEl.textContent = '文件不可预览';
        if (timeEl) timeEl.textContent = '00:00 / 00:00';
        _isPlaying = false;
        _updatePlayIcon();
    });

    // Volume
    if (volumeEl) {
        _audio.volume = parseFloat(volumeEl.value) || 0.8;
        volumeEl.addEventListener('input', function () {
            _audio.volume = parseFloat(this.value) || 0;
        });
    }

    // Expose globally so inline scripts (library/editor) can use it
    window.playAudio = playAudio;
    window.ammPlayer = { play: function (filePath) { playAudio(filePath, filePath); } };

    /* ================================================================
       HELPERS
       ================================================================ */
    function _fetchJSON(url) {
        return fetch(url).then(function (resp) {
            return resp.json().catch(function () { return {}; }).then(function (data) {
                if (!resp.ok) {
                    var detail = data.detail || data.message || data.error || ('HTTP ' + resp.status);
                    if (Array.isArray(detail)) detail = detail.map(function (item) { return item.msg || item.message || String(item); }).join('; ');
                    if (typeof detail === 'object') detail = JSON.stringify(detail);
                    throw new Error(detail);
                }
                return data;
            });
        });
    }

    function addNonEmpty(params, key, value) {
        if (value == null) return;
        value = String(value).trim();
        if (value) params.set(key, value);
    }

    function _escapeHTML(str) {
        if (str == null) return '';
        return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;');
    }

    function _formatBytes(bytes) {
        if (bytes == null) return '--';
        bytes = Number(bytes);
        if (bytes === 0) return '0 B';
        var k = 1024, sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        var i = Math.floor(Math.log(bytes) / Math.log(k));
        return (bytes / Math.pow(k, i)).toFixed(1) + ' ' + sizes[i];
    }

    function _formatDuration(sec) {
        if (sec == null) return '--';
        sec = Number(sec);
        if (sec < 60) return sec.toFixed(1) + 's';
        var m = Math.floor(sec / 60);
        var s = Math.floor(sec % 60);
        return m + 'm ' + s + 's';
    }

    /* ================================================================
       3. DASHBOARD — dashboardInit()
       ================================================================ */
    function dashboardInit() {
        _loadReport();
        _loadRecentFiles();
        _initDashboardSearch();
    }

    function _loadReport() {
        _fetchJSON('/api/report').then(function (data) {
            var el;

            el = document.getElementById('stat-total-files');
            if (el) el.textContent = data.total_files != null ? data.total_files : '--';

            el = document.getElementById('stat-formats');
            if (el) {
                var fmtCount = 0;
                if (data.format_distribution) {
                    fmtCount = typeof data.format_distribution === 'object' ? Object.keys(data.format_distribution).length : 0;
                }
                el.textContent = fmtCount || '--';
            }

            el = document.getElementById('stat-avg-duration');
            if (el) el.textContent = data.avg_duration != null ? _formatDuration(data.avg_duration) : '--';

            el = document.getElementById('stat-total-size');
            if (el) el.textContent = data.total_size != null ? _formatBytes(data.total_size) : '--';
        }).catch(function (err) {
            console.warn('Report API not available:', err);
        });
    }

    function _loadRecentFiles() {
        _fetchJSON('/api/search?q=*&limit=10').then(function (data) {
            var files = data.results || [];
            var tbody = document.getElementById('recent-files-body');
            if (!tbody) return;

            if (files.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" class="px-5 py-10 text-center text-on-surface-variant">No files found. Run a scan to populate your library.</td></tr>';
                return;
            }
            tbody.innerHTML = files.map(function (f) {
                return '<tr class="border-b border-outline-variant/10 hover:bg-surface-container-low transition-colors">' +
                    '<td class="px-5 py-3 text-on-surface truncate max-w-xs">' + _escapeHTML(f.filename || f.name || '--') + '</td>' +
                    '<td class="px-5 py-3 text-on-surface-variant">' + _escapeHTML(f.format || '--') + '</td>' +
                    '<td class="px-5 py-3 text-on-surface-variant font-mono">' + _escapeHTML(f.duration || '--') + '</td>' +
                    '<td class="px-5 py-3 text-on-surface-variant">' + (f.tempo ? _escapeHTML(f.tempo) + ' BPM' : '--') + '</td>' +
                    '<td class="px-5 py-3 text-on-surface-variant">' + _formatBytes(f.size) + '</td>' +
                    '</tr>';
            }).join('');
        }).catch(function (err) {
            console.warn('Search API not available for recent files:', err);
        });
    }

    function _initDashboardSearch() {
        var qs = document.getElementById('quick-search');
        if (qs) {
            qs.addEventListener('keydown', function (e) {
                if (e.key === 'Enter' && this.value.trim()) {
                    window.location.href = '/library?q=' + encodeURIComponent(this.value.trim());
                }
            });
        }
    }

    /* ================================================================
       4. LIBRARY — libraryInit()
       ================================================================ */
    var libState = { page: 1, perPage: 25, total: 0, query: '' };

    function libraryInit() {
        var urlParams = new URLSearchParams(window.location.search);
        var q = urlParams.get('q');
        if (q) {
            var searchInput = document.getElementById('lib-search');
            if (searchInput) searchInput.value = q;
            libState.query = q;
            _librarySearch();
        }

        // Form submission
        var form = document.getElementById('search-form');
        if (form) {
            form.addEventListener('submit', function (e) {
                e.preventDefault();
                libState.page = 1;
                libState.query = (document.getElementById('lib-search') || {}).value || '';
                _librarySearch();
            });
        }

        // Clear button
        var clearBtn = document.getElementById('btn-clear');
        if (clearBtn) {
            clearBtn.addEventListener('click', function () {
                ['lib-search', 'filter-format', 'filter-brightness', 'filter-tempo-min', 'filter-tempo-max'].forEach(function (id) {
                    var el = document.getElementById(id);
                    if (el) el.value = '';
                });
                libState.page = 1;
                libState.query = '';
                _librarySearch();
            });
        }

        // Pagination
        var prevBtn = document.getElementById('btn-prev');
        var nextBtn = document.getElementById('btn-next');
        if (prevBtn) {
            prevBtn.addEventListener('click', function () {
                if (libState.page > 1) { libState.page--; _librarySearch(); }
            });
        }
        if (nextBtn) {
            nextBtn.addEventListener('click', function () {
                var totalPages = Math.max(1, Math.ceil(libState.total / libState.perPage));
                if (libState.page < totalPages) { libState.page++; _librarySearch(); }
            });
        }
    }

    function _librarySearch() {
        var tbody = document.getElementById('results-body');
        if (!tbody) return;

        // Build query string
        var searchVal = (document.getElementById('lib-search') || {}).value || libState.query;
        var params = new URLSearchParams();
        addNonEmpty(params, 'q', searchVal);

        var fmt = (document.getElementById('filter-format') || {}).value;
        addNonEmpty(params, 'format', fmt);

        var brightness = (document.getElementById('filter-brightness') || {}).value;
        addNonEmpty(params, 'brightness', brightness);

        var tempoMin = (document.getElementById('filter-tempo-min') || {}).value;
        addNonEmpty(params, 'min_bpm', tempoMin);

        var tempoMax = (document.getElementById('filter-tempo-max') || {}).value;
        addNonEmpty(params, 'max_bpm', tempoMax);

        params.set('limit', libState.perPage);
        params.set('offset', (libState.page - 1) * libState.perPage);

        tbody.innerHTML = '<tr><td colspan="6" class="px-5 py-10 text-center text-on-surface-variant"><span class="material-symbols-outlined animate-spin text-2xl">sync</span></td></tr>';

        _fetchJSON('/api/search?' + params.toString()).then(function (data) {
            var files = data.results || [];
            libState.total = data.total || files.length;
            var totalPages = Math.max(1, Math.ceil(libState.total / libState.perPage));

            var countEl = document.getElementById('result-count');
            if (countEl) countEl.textContent = libState.total + ' items';

            var pageInfo = document.getElementById('page-info');
            if (pageInfo) pageInfo.textContent = 'Page ' + libState.page + ' of ' + totalPages;

            var prevBtn = document.getElementById('btn-prev');
            var nextBtn = document.getElementById('btn-next');
            if (prevBtn) prevBtn.disabled = libState.page <= 1;
            if (nextBtn) nextBtn.disabled = libState.page >= totalPages;

            if (files.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" class="px-5 py-10 text-center text-on-surface-variant">No results found.</td></tr>';
                return;
            }

            tbody.innerHTML = files.map(function (f) {
                var meta = f.metadata || {};
                var filePath = f.file_path || f.path || meta.path || f.id || '';
                var fileName = f.filename || f.file_name || f.name || '--';
                var tags = (f.tags || meta.tags || []).slice(0, 3).map(function (t) {
                    return '<span class="inline-block px-2 py-0.5 bg-secondary-container text-on-secondary-container rounded text-xs mr-1">' + _escapeHTML(t) + '</span>';
                }).join('');

                return '<tr class="border-b border-outline-variant/10 hover:bg-surface-container-low transition-colors group">' +
                    '<td class="px-3 py-3">' +
                        '<button onclick="playAudio(\'' + _escapeHTML(filePath).replace(/'/g, "\\'") + '\', \'' + _escapeHTML(fileName).replace(/'/g, "\\'") + '\')" ' +
                        'class="w-8 h-8 flex items-center justify-center rounded-full bg-surface-container-high hover:bg-primary/20 transition-colors opacity-0 group-hover:opacity-100 cursor-pointer">' +
                            '<span class="material-symbols-outlined text-on-surface text-sm">play_arrow</span>' +
                        '</button>' +
                    '</td>' +
                    '<td class="px-5 py-3 text-on-surface truncate max-w-xs">' + _escapeHTML(fileName) + '</td>' +
                    '<td class="px-5 py-3"><span class="px-2 py-0.5 bg-surface-container-high rounded text-xs font-medium text-on-surface-variant">' + _escapeHTML(f.format || meta.format || '--') + '</span></td>' +
                    '<td class="px-5 py-3 text-on-surface-variant font-mono">' + _escapeHTML(f.duration || meta.duration || '--') + '</td>' +
                    '<td class="px-5 py-3 text-on-surface-variant">' + (f.tempo || meta.bpm ? _escapeHTML(f.tempo || meta.bpm) + ' BPM' : '--') + '</td>' +
                    '<td class="px-5 py-3 text-on-surface-variant">' + tags + '</td>' +
                    '</tr>';
            }).join('');
        }).catch(function (err) {
            tbody.innerHTML = '<tr><td colspan="6" class="px-5 py-10 text-center text-error">' + _escapeHTML(err.message || 'Error loading results.') + '</td></tr>';
            console.warn('Library search error:', err);
        });
    }

    /* ================================================================
       5. EDITOR — editorInit()
       ================================================================ */
    var editorState = { selectedId: null, selectedData: null, searchTimeout: null };

    function editorInit() {
        var searchInput = document.getElementById('editor-search');
        if (searchInput) {
            searchInput.addEventListener('input', function () {
                clearTimeout(editorState.searchTimeout);
                var q = this.value.trim();
                editorState.searchTimeout = setTimeout(function () { _editorSearch(q); }, 300);
            });
        }

        // Save form
        var form = document.getElementById('editor-form');
        if (form) {
            form.addEventListener('submit', function (e) {
                e.preventDefault();
                _editorSave();
            });
        }

        // Revert button
        var revertBtn = document.getElementById('btn-revert');
        if (revertBtn) {
            revertBtn.addEventListener('click', function () {
                if (editorState.selectedData) {
                    var d = editorState.selectedData;
                    var notesEl = document.getElementById('edit-notes');
                    var tagsEl = document.getElementById('edit-tags');
                    if (notesEl) notesEl.value = d.notes || '';
                    if (tagsEl) tagsEl.value = (d.tags || []).join(', ');
                    _editorStatus('Reverted.');
                }
            });
        }
    }

    function _editorSearch(query) {
        var list = document.getElementById('editor-file-list');
        if (!list) return;

        if (!query) {
            list.innerHTML = '<div class="text-center py-8 text-on-surface-variant text-sm">' +
                '<span class="material-symbols-outlined text-2xl block mb-1 opacity-50">folder_open</span>Search to find files</div>';
            return;
        }

        list.innerHTML = '<div class="text-center py-8"><span class="material-symbols-outlined text-2xl animate-spin text-on-surface-variant">sync</span></div>';

        _fetchJSON('/api/search?q=' + encodeURIComponent(query) + '&limit=50').then(function (data) {
            var files = data.results || [];
            if (files.length === 0) {
                list.innerHTML = '<div class="text-center py-8 text-on-surface-variant text-sm">No files found.</div>';
                return;
            }

            list.innerHTML = files.map(function (f) {
                var id = f.id || f.file_path || f.path || '';
                var name = f.filename || f.name || '--';
                return '<button onclick="_editorSelectFile(\'' + _escapeHTML(id).replace(/'/g, "\\'") + '\')" ' +
                    'class="w-full text-left px-3 py-2 rounded-lg text-sm text-on-surface-variant hover:bg-surface-container-high transition-colors flex items-center gap-2 file-item" ' +
                    'data-id="' + _escapeHTML(id) + '">' +
                    '<span class="material-symbols-outlined text-base opacity-60">audio_file</span>' +
                    '<span class="truncate">' + _escapeHTML(name) + '</span>' +
                    '</button>';
            }).join('');
        }).catch(function (err) {
            list.innerHTML = '<div class="text-center py-8 text-error text-sm">Search error.</div>';
            console.warn('Editor search error:', err);
        });
    }

    function _editorSelectFile(id) {
        // Highlight active
        document.querySelectorAll('.file-item').forEach(function (el) {
            el.classList.remove('bg-surface-container-highest', 'text-primary');
        });
        var active = document.querySelector('.file-item[data-id="' + CSS.escape(id) + '"]');
        if (active) active.classList.add('bg-surface-container-highest', 'text-primary');

        editorState.selectedId = id;
        document.getElementById('edit-file-id').value = id;

        // Load full metadata from /api/sample/{id}
        _fetchJSON('/api/sample/' + encodeURIComponent(id)).then(function (f) {
            editorState.selectedData = f;

            // Populate read-only fields
            var set = function (eid, val) {
                var el = document.getElementById(eid);
                if (el) el.textContent = val;
            };
            set('meta-filename', f.filename || f.name || '--');
            set('meta-format', f.format || '--');
            set('meta-duration', f.duration || '--');
            set('meta-samplerate', f.sample_rate || '--');
            set('meta-channels', f.channels || '--');
            set('meta-tempo', f.tempo != null ? f.tempo + ' BPM' : '--');
            set('meta-key', f.key || '--');
            set('meta-brightness', f.brightness || '--');
            set('meta-filesize', _formatBytes(f.file_size || f.size));

            // Auto tags
            var tagsDiv = document.getElementById('meta-tags');
            if (tagsDiv) {
                if (f.tags && f.tags.length) {
                    tagsDiv.innerHTML = f.tags.map(function (t) {
                        return '<span class="px-2 py-0.5 bg-secondary-container text-on-secondary-container rounded text-xs">' + _escapeHTML(t) + '</span>';
                    }).join('');
                } else {
                    tagsDiv.innerHTML = '<span class="text-xs text-on-surface-variant">None</span>';
                }
            }

            // Edit form pre-fill
            var notesEl = document.getElementById('edit-notes');
            if (notesEl) notesEl.value = f.notes || '';

            var tagsInput = document.getElementById('edit-tags');
            if (tagsInput) tagsInput.value = (f.tags || []).join(', ');

            // Manual tags display
            var mtDiv = document.getElementById('current-manual-tags');
            var mtDisplay = document.getElementById('manual-tags-display');
            if (f.manual_tags && f.manual_tags.length) {
                if (mtDiv) mtDiv.classList.remove('hidden');
                if (mtDisplay) {
                    mtDisplay.innerHTML = f.manual_tags.map(function (t) {
                        return '<span class="px-2 py-0.5 bg-tertiary/20 text-tertiary rounded text-xs">' + _escapeHTML(t) + '</span>';
                    }).join('');
                }
            } else {
                if (mtDiv) mtDiv.classList.add('hidden');
            }

            // Show play button
            var playSelected = document.getElementById('btn-play-selected');
            if (playSelected) {
                playSelected.classList.remove('hidden');
                playSelected.onclick = function () {
                    playAudio(f.file_path || f.path || id, f.filename || f.name);
                };
            }
        }).catch(function (err) {
            console.warn('Failed to load sample metadata:', err);
        });
    }

    function _editorSave() {
        var id = editorState.selectedId;
        if (!id) return;

        var notes = (document.getElementById('edit-notes') || {}).value || '';
        var tagsRaw = (document.getElementById('edit-tags') || {}).value || '';
        var tags = tagsRaw ? tagsRaw.split(',').map(function (t) { return t.trim(); }).filter(Boolean) : [];

        var btn = document.getElementById('btn-save');
        if (btn) btn.disabled = true;
        _editorStatus('Saving...');

        fetch('/api/sample/' + encodeURIComponent(id) + '/review', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ notes: notes.trim(), tags: tags, overrides: {} })
        }).then(function (resp) {
            if (resp.ok) {
                _editorStatus('Saved!');
            } else {
                _editorStatus('Error saving.');
            }
        }).catch(function () {
            _editorStatus('Network error.');
        }).finally(function () {
            if (btn) btn.disabled = false;
        });
    }

    function _editorStatus(msg) {
        var el = document.getElementById('save-status');
        if (el) {
            el.textContent = msg;
            el.classList.remove('text-error');
            if (msg && msg.indexOf('Error') !== -1) el.classList.add('text-error');
            if (msg) setTimeout(function () { el.textContent = ''; }, 3000);
        }
    }

    // Expose for inline onclick handlers
    window._editorSelectFile = _editorSelectFile;

    /* ================================================================
       6. SETTINGS — settingsInit()
       ================================================================ */
    function settingsInit() {
        // Copy buttons already wired via inline onclick="copyToClipboard(...)" in template.
        // Load settings data
        _fetchJSON('/api/settings').then(function (data) {
            var set = function (eid, val) {
                var el = document.getElementById(eid);
                if (el) el.textContent = val;
            };
            set('library-path', data.library_path || 'Not configured');
            set('sample-dir', data.sample_dir || 'Not configured');
            set('db-path', data.db_path || 'Not configured');
            set('db-records', data.total_records != null ? data.total_records : '--');
            set('last-scan', data.last_scan || 'Never');
        }).catch(function (err) {
            console.warn('Settings API not available:', err);
            ['library-path', 'sample-dir'].forEach(function (id) {
                var el = document.getElementById(id);
                if (el) el.textContent = 'Unable to load';
            });
        });
    }

    // Expose copyToClipboard for settings page inline onclick
    window.copyToClipboard = function (elementId) {
        var el = document.getElementById(elementId);
        if (!el) return;
        var text = el.textContent;
        navigator.clipboard.writeText(text).then(function () {
            // Brief visual feedback — find the sibling button's icon
            var parent = el.closest('.flex');
            if (parent) {
                var icon = parent.querySelector('.material-symbols-outlined');
                if (icon) {
                    var original = icon.textContent;
                    icon.textContent = 'check';
                    setTimeout(function () { icon.textContent = original; }, 1500);
                }
            }
        });
    };

    /* ================================================================
       EXPOSE INIT FUNCTIONS GLOBALLY
       Each page template calls its init from {% block scripts %}.
       ================================================================ */
    window.dashboardInit = dashboardInit;
    window.libraryInit   = libraryInit;
    window.editorInit    = editorInit;
    window.settingsInit  = settingsInit;

})();

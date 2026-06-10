/**
 * app.js — Audio Metadata Manager (AMM) Web UI
 * Loaded globally via base.html. Provides:
 *   - Global search (top bar)
 *   - Global audio player with waveform visualization
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

        // Keyboard shortcut: Cmd+K / Ctrl+K to focus search
        document.addEventListener('keydown', function (e) {
            if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
                e.preventDefault();
                globalSearch.focus();
            }
        });
    }

    /* ================================================================
       2. WAVEFORM VISUALIZATION
       ================================================================ */
    const WaveformRenderer = {
        canvas: null,
        ctx: null,
        audioContext: null,
        analyser: null,
        dataArray: null,
        animationId: null,

        init: function (canvasId) {
            this.canvas = document.getElementById(canvasId);
            if (!this.canvas) return;
            this.ctx = this.canvas.getContext('2d');
            this.resize();
            window.addEventListener('resize', () => this.resize());
        },

        resize: function () {
            if (!this.canvas) return;
            const rect = this.canvas.parentElement.getBoundingClientRect();
            this.canvas.width = rect.width * window.devicePixelRatio;
            this.canvas.height = rect.height * window.devicePixelRatio;
            this.ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
            this.canvas.style.width = rect.width + 'px';
            this.canvas.style.height = rect.height + 'px';
        },

        connectAudio: function (audioElement) {
            if (!this.audioContext) {
                this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            }
            if (!this.analyser) {
                this.analyser = this.audioContext.createAnalyser();
                this.analyser.fftSize = 256;
                const bufferLength = this.analyser.frequencyBinCount;
                this.dataArray = new Uint8Array(bufferLength);
            }
            const source = this.audioContext.createMediaElementSource(audioElement);
            source.connect(this.analyser);
            this.analyser.connect(this.audioContext.destination);
        },

        draw: function () {
            if (!this.ctx || !this.analyser) {
                this.drawPlaceholder();
                return;
            }

            this.animationId = requestAnimationFrame(() => this.draw());

            this.analyser.getByteFrequencyData(this.dataArray);

            const width = this.canvas.width / window.devicePixelRatio;
            const height = this.canvas.height / window.devicePixelRatio;
            const barWidth = (width / this.dataArray.length) * 2.5;
            let x = 0;

            this.ctx.clearRect(0, 0, width, height);

            for (let i = 0; i < this.dataArray.length; i++) {
                const barHeight = (this.dataArray[i] / 255) * height;

                // Gradient color based on frequency
                const hue = (i / this.dataArray.length) * 120; // Orange to Cyan
                const gradient = this.ctx.createLinearGradient(x, height, x, height - barHeight);
                gradient.addColorStop(0, `hsla(${hue + 20}, 100%, 60%, 0.8)`);
                gradient.addColorStop(1, `hsla(${hue + 20}, 100%, 70%, 0.4)`);

                this.ctx.fillStyle = gradient;
                this.ctx.fillRect(x, height - barHeight, barWidth - 1, barHeight);

                x += barWidth;
            }
        },

        drawPlaceholder: function () {
            if (!this.ctx) return;
            const width = this.canvas.width / window.devicePixelRatio;
            const height = this.canvas.height / window.devicePixelRatio;

            this.ctx.clearRect(0, 0, width, height);

            // Draw static waveform bars
            const barCount = 64;
            const barWidth = (width / barCount) * 0.8;
            const gap = (width / barCount) * 0.2;

            for (let i = 0; i < barCount; i++) {
                const barHeight = Math.random() * height * 0.6 + height * 0.1;
                const x = i * (barWidth + gap);

                // Gradient from orange (low) to cyan (mid) to blue (high)
                const ratio = i / barCount;
                let color;
                if (ratio < 0.33) {
                    color = '#FF6B35'; // Low freq - orange
                } else if (ratio < 0.66) {
                    color = '#00D4AA'; // Mid freq - cyan
                } else {
                    color = '#4A9EFF'; // High freq - blue
                }

                this.ctx.fillStyle = color;
                this.ctx.globalAlpha = 0.3;
                this.ctx.fillRect(x, height - barHeight, barWidth, barHeight);
            }
            this.ctx.globalAlpha = 1;
        },

        stop: function () {
            if (this.animationId) {
                cancelAnimationFrame(this.animationId);
                this.animationId = null;
            }
        },

        clear: function () {
            this.stop();
            if (this.ctx) {
                const width = this.canvas.width / window.devicePixelRatio;
                const height = this.canvas.height / window.devicePixelRatio;
                this.ctx.clearRect(0, 0, width, height);
            }
        }
    };

    /* ================================================================
       3. GLOBAL AUDIO PLAYER
       ================================================================ */
    const _audio = new Audio();
    _audio.preload = 'metadata';
    let _isPlaying = false;
    let _audioConnected = false;

    const playerEl = document.getElementById('audio-player');
    const playBtn = document.getElementById('player-play');
    const filenameEl = document.getElementById('player-filename');
    const timeEl = document.getElementById('player-time');
    const volumeEl = document.getElementById('player-volume');
    const expandBtn = document.getElementById('player-expand');
    const waveformProgress = document.getElementById('waveform-progress');

    // Initialize waveform
    WaveformRenderer.init('waveform-canvas');
    WaveformRenderer.drawPlaceholder();

    /**
     * playAudio(filePath, fileName)
     * Shows the bottom player bar and starts streaming /api/audio/{filePath}.
     */
    function playAudio(filePath, fileName) {
        if (!playerEl || !_audio) return;
        playerEl.classList.remove('hidden');
        if (filenameEl) filenameEl.textContent = fileName || filePath;

        // Connect audio to waveform on first play
        if (!_audioConnected) {
            try {
                WaveformRenderer.connectAudio(_audio);
                _audioConnected = true;
            } catch (e) {
                console.warn('Waveform connection failed:', e);
            }
        }

        _audio.src = '/api/audio/' + encodeURIComponent(filePath);
        _audio.play().then(function () {
            _isPlaying = true;
            _updatePlayIcon();
            WaveformRenderer.draw();

            // Highlight playing card
            document.querySelectorAll('.result-card').forEach(card => card.classList.remove('playing'));
            const playingCard = document.querySelector(`[data-file="${filePath}"]`)?.closest('.result-card');
            if (playingCard) playingCard.classList.add('playing');
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

        // Update play button state
        if (_isPlaying) {
            playBtn.classList.add('active');
        } else {
            playBtn.classList.remove('active');
        }
    }

    if (playBtn) {
        playBtn.addEventListener('click', function () {
            if (!_audio.src) return;
            if (_isPlaying) {
                _audio.pause();
                _isPlaying = false;
                WaveformRenderer.stop();
            } else {
                _audio.play().catch(function () {});
                _isPlaying = true;
                WaveformRenderer.draw();
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

        // Update waveform progress
        if (waveformProgress && _audio.duration) {
            const progress = (_audio.currentTime / _audio.duration) * 100;
            waveformProgress.style.width = progress + '%';
        }
    });

    _audio.addEventListener('loadedmetadata', function () {
        if (timeEl) timeEl.textContent = '00:00 / ' + _formatTime(_audio.duration);
    });

    _audio.addEventListener('ended', function () {
        _isPlaying = false;
        _updatePlayIcon();
        WaveformRenderer.stop();
    });

    _audio.addEventListener('error', function () {
        if (filenameEl) filenameEl.textContent = '文件不可预览';
        if (timeEl) timeEl.textContent = '00:00 / 00:00';
        _isPlaying = false;
        _updatePlayIcon();
        WaveformRenderer.stop();
    });

    // Volume
    if (volumeEl) {
        _audio.volume = parseFloat(volumeEl.value) || 0.8;
        volumeEl.addEventListener('input', function () {
            _audio.volume = parseFloat(this.value) || 0;
        });
    }

    // Expand/Collapse mini player
    if (expandBtn && playerEl) {
        let isExpanded = false;
        expandBtn.addEventListener('click', function () {
            isExpanded = !isExpanded;
            playerEl.classList.toggle('expanded', isExpanded);
            const icon = expandBtn.querySelector('.material-symbols-outlined');
            if (icon) icon.textContent = isExpanded ? 'expand_more' : 'expand_less';

            // Resize waveform after animation
            setTimeout(() => WaveformRenderer.resize(), 300);
        });
    }

    // Waveform click to seek
    const waveformContainer = document.getElementById('waveform-container');
    if (waveformContainer) {
        waveformContainer.addEventListener('click', function (e) {
            if (!_audio.duration) return;
            const rect = this.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const progress = x / rect.width;
            _audio.currentTime = progress * _audio.duration;
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

    // Tag dimension helper
    function _getTagDimension(tag) {
        const techTags = ['bpm', 'lufs', 'sample rate', 'bit depth', 'tempo', 'key', '44.1khz', '48khz', '96khz'];
        const emotionTags = ['dark', 'bright', 'calm', 'energetic', 'warm', 'cold', 'aggressive', 'peaceful', 'melancholic', 'uplifting'];
        const categoryTags = ['loop', 'one-shot', 'oneshot', 'percussive', 'sustained', 'bass', 'lead', 'pad', 'fx', 'vocal', 'drums', 'strings'];
        const formatTags = ['wav', 'mp3', 'flac', 'aiff', 'ogg', 'aac', 'm4a', '24-bit', '16-bit', '32-bit'];

        const lower = tag.toLowerCase();
        if (techTags.some(t => lower.includes(t))) return 'tech';
        if (emotionTags.some(t => lower.includes(t))) return 'emotion';
        if (formatTags.some(t => lower.includes(t))) return 'format';
        if (categoryTags.some(t => lower.includes(t))) return 'category';
        return 'category';
    }

    function _renderTagPill(tag) {
        const dim = _getTagDimension(tag);
        return '<span class="tag-pill tag-pill--' + dim + '">' + _escapeHTML(tag) + '</span>';
    }

    /* ================================================================
       4. DASHBOARD — dashboardInit()
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
                tbody.innerHTML = '<tr><td colspan="6" class="px-lg py-xl text-center text-text-tertiary">No files found. Run a scan to populate your library.</td></tr>';
                return;
            }
            tbody.innerHTML = files.map(function (f) {
                var tags = (f.tags || []).slice(0, 3).map(_renderTagPill).join('');
                var moreTags = (f.tags || []).length > 3 ? '<span class="text-xs text-text-tertiary">+' + ((f.tags || []).length - 3) + '</span>' : '';
                var filePath = f.file_path || f.path || f.id || '';
                var fileName = f.filename || f.name || '--';

                return '<tr class="hover:bg-bg-elevated transition-colors">' +
                    '<td class="px-md py-sm">' +
                        '<div class="flex items-center gap-sm">' +
                            '<button onclick="playAudio(\'' + _escapeHTML(filePath).replace(/'/g, "\\'") + '\', \'' + _escapeHTML(fileName).replace(/'/g, "\\'") + '\')" ' +
                            'class="play-button w-8 h-8 flex items-center justify-center">' +
                                '<span class="material-symbols-outlined text-sm">play_arrow</span>' +
                            '</button>' +
                            '<span class="text-text-primary truncate max-w-xs">' + _escapeHTML(fileName) + '</span>' +
                        '</div>' +
                    '</td>' +
                    '<td class="px-md py-sm"><span class="tag-pill tag-pill--format">' + _escapeHTML(f.format || '--') + '</span></td>' +
                    '<td class="px-md py-sm font-mono text-text-secondary">' + _escapeHTML(f.duration || '--') + '</td>' +
                    '<td class="px-md py-sm font-mono text-text-secondary">' + (f.tempo ? _escapeHTML(f.tempo) + ' BPM' : '--') + '</td>' +
                    '<td class="px-md py-sm text-text-secondary">' + _formatBytes(f.size) + '</td>' +
                    '<td class="px-md py-sm"><div class="flex flex-wrap gap-xs">' + tags + moreTags + '</div></td>' +
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
       5. LIBRARY — libraryInit()
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

        // Filter chips
        document.querySelectorAll('.filter-chip').forEach(chip => {
            chip.addEventListener('click', function () {
                const filterGroup = this.dataset.filter;
                const isActive = this.classList.contains('active');

                // Deactivate all in same group
                document.querySelectorAll('.filter-chip[data-filter="' + filterGroup + '"]').forEach(c => {
                    c.classList.remove('active');
                });

                // Activate clicked (or keep "all" if clicking same)
                if (!isActive || this.dataset.value === 'all') {
                    this.classList.add('active');
                } else {
                    document.querySelector('.filter-chip[data-filter="' + filterGroup + '"][data-value="all"]').classList.add('active');
                }

                // Trigger search
                libState.page = 1;
                _librarySearch();
            });
        });

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
        var resultsBody = document.getElementById('results-body');
        if (!resultsBody) return;

        // Build query string
        var searchVal = (document.getElementById('lib-search') || {}).value || libState.query;
        var params = new URLSearchParams();
        addNonEmpty(params, 'q', searchVal);

        // Get active filter values
        var formatChip = document.querySelector('.filter-chip[data-filter="format"].active');
        if (formatChip && formatChip.dataset.value !== 'all') {
            params.set('format', formatChip.dataset.value);
        }

        var brightnessChip = document.querySelector('.filter-chip[data-filter="brightness"].active');
        if (brightnessChip && brightnessChip.dataset.value !== 'all') {
            params.set('brightness', brightnessChip.dataset.value);
        }

        var tempoMin = (document.getElementById('filter-tempo-min') || {}).value;
        addNonEmpty(params, 'min_bpm', tempoMin);

        var tempoMax = (document.getElementById('filter-tempo-max') || {}).value;
        addNonEmpty(params, 'max_bpm', tempoMax);

        params.set('limit', libState.perPage);
        params.set('offset', (libState.page - 1) * libState.perPage);

        resultsBody.innerHTML = '<div class="px-lg py-xl text-center"><div class="spinner mx-auto mb-md"></div><p class="text-sm text-text-secondary">Searching...</p></div>';

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
                resultsBody.innerHTML = '<div class="px-lg py-xl text-center text-text-tertiary">' +
                    '<span class="material-symbols-outlined text-4xl block mb-md opacity-50">search_off</span>' +
                    '<p class="text-sm">No results found.</p>' +
                    '<p class="text-xs mt-xs">Try different keywords or filters.</p></div>';
                return;
            }

            resultsBody.innerHTML = files.map(function (f) {
                var meta = f.metadata || {};
                var filePath = f.file_path || f.path || meta.path || f.id || '';
                var fileName = f.filename || f.file_name || f.name || '--';
                var tags = (f.tags || meta.tags || []).slice(0, 4).map(_renderTagPill).join('');
                var moreTags = (f.tags || meta.tags || []).length > 4 ? '<span class="text-xs text-text-tertiary">+' + ((f.tags || meta.tags || []).length - 4) + '</span>' : '';

                return '<div class="result-card flex items-center gap-md px-lg py-md hover:bg-bg-elevated transition-colors cursor-pointer">' +
                    '<button onclick="playAudio(\'' + _escapeHTML(filePath).replace(/'/g, "\\'") + '\', \'' + _escapeHTML(fileName).replace(/'/g, "\\'") + '\')" ' +
                    'class="play-button w-9 h-9 flex-shrink-0 flex items-center justify-center" data-file="' + _escapeHTML(filePath) + '">' +
                        '<span class="material-symbols-outlined text-sm">play_arrow</span>' +
                    '</button>' +
                    '<div class="w-24 h-12 bg-bg-base rounded overflow-hidden flex-shrink-0">' +
                        '<div class="w-full h-full bg-gradient-to-r from-waveform-low via-waveform-mid to-waveform-high opacity-30"></div>' +
                    '</div>' +
                    '<div class="flex-1 min-w-0">' +
                        '<p class="text-sm font-medium text-text-primary truncate">' + _escapeHTML(fileName) + '</p>' +
                        '<div class="flex items-center gap-md mt-xs">' +
                            '<span class="text-xs font-mono text-text-secondary">' + _escapeHTML(f.duration || meta.duration || '--') + '</span>' +
                            '<span class="text-xs font-mono text-text-secondary">' + (f.tempo || meta.bpm ? _escapeHTML(f.tempo || meta.bpm) + ' BPM' : '--') + '</span>' +
                            '<span class="text-xs text-text-tertiary">' + _formatBytes(f.size || meta.file_size) + '</span>' +
                        '</div>' +
                    '</div>' +
                    '<div class="flex flex-wrap gap-xs flex-shrink-0">' + tags + moreTags + '</div>' +
                    '<span class="tag-pill tag-pill--format flex-shrink-0">' + _escapeHTML(f.format || meta.format || '--') + '</span>' +
                    '</div>';
            }).join('');
        }).catch(function (err) {
            resultsBody.innerHTML = '<div class="px-lg py-xl text-center text-error">' +
                '<span class="material-symbols-outlined text-4xl block mb-md">error</span>' +
                '<p class="text-sm">Search failed. Please try again.</p></div>';
            console.warn('Library search error:', err);
        });
    }

    /* ================================================================
       6. EDITOR — editorInit()
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
            list.innerHTML = '<div class="text-center py-8 text-text-tertiary text-sm">' +
                '<span class="material-symbols-outlined text-2xl block mb-1 opacity-50">folder_open</span>Search to find files</div>';
            return;
        }

        list.innerHTML = '<div class="text-center py-8"><div class="spinner mx-auto"></div></div>';

        _fetchJSON('/api/search?q=' + encodeURIComponent(query) + '&limit=50').then(function (data) {
            var files = data.results || [];
            if (files.length === 0) {
                list.innerHTML = '<div class="text-center py-8 text-text-tertiary text-sm">No files found.</div>';
                return;
            }

            list.innerHTML = files.map(function (f) {
                var id = f.id || f.file_path || f.path || '';
                var name = f.filename || f.name || '--';
                return '<button onclick="_editorSelectFile(\'' + _escapeHTML(id).replace(/'/g, "\\'") + '\')" ' +
                    'class="w-full text-left px-md py-sm rounded-lg text-sm text-text-secondary hover:bg-bg-elevated transition-colors flex items-center gap-sm file-item" ' +
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
            el.classList.remove('bg-bg-elevated', 'text-text-primary');
        });
        var active = document.querySelector('.file-item[data-id="' + CSS.escape(id) + '"]');
        if (active) active.classList.add('bg-bg-elevated', 'text-text-primary');

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
                    tagsDiv.innerHTML = f.tags.map(_renderTagPill).join('');
                } else {
                    tagsDiv.innerHTML = '<span class="text-xs text-text-tertiary">None</span>';
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
                    mtDisplay.innerHTML = f.manual_tags.map(_renderTagPill).join('');
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
       7. SETTINGS — settingsInit()
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
    window.libraryInit = libraryInit;
    window.editorInit = editorInit;
    window.settingsInit = settingsInit;

})();

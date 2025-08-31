// 联通网盘 Web 版 JavaScript
class WoPanWeb {
    constructor() {
        this.currentFolderId = '0';
        this.currentPath = '根目录';
        this.folderHistory = [];
        this.selectedFile = null;
        this.isConnected = false;
        
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Token 连接
        document.getElementById('connectBtn').addEventListener('click', () => this.connectAPI());
        document.getElementById('tokenInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.connectAPI();
        });

        // 导航按钮
        document.getElementById('backBtn').addEventListener('click', () => this.goBack());
        document.getElementById('refreshBtn').addEventListener('click', () => this.refreshCurrentFolder());

        // 文件上传
        const fileInput = document.getElementById('fileInput');
        const folderInput = document.getElementById('folderInput');
        const uploadArea = document.getElementById('uploadArea');

        fileInput.addEventListener('change', (e) => this.handleFileSelect(e.target.files, 'files'));
        folderInput.addEventListener('change', (e) => this.handleFileSelect(e.target.files, 'folder'));

        // 拖拽上传
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');

            // 处理拖拽的文件和文件夹
            const items = e.dataTransfer.items;
            if (items) {
                this.handleDragDropItems(items);
            } else {
                this.handleFileSelect(e.dataTransfer.files, 'files');
            }
        });

        // 下载和删除按钮
        document.getElementById('downloadBtn').addEventListener('click', () => this.getDownloadLink());
        document.getElementById('deleteBtn').addEventListener('click', () => this.deleteFile());

        // 创建文件夹按钮
        document.getElementById('createFolderBtn').addEventListener('click', () => this.showCreateFolderModal());
        document.getElementById('confirmCreateFolderBtn').addEventListener('click', () => this.createFolder());
        document.getElementById('folderNameInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.createFolder();
        });

        // 播放列表生成按钮
        document.getElementById('generatePlaylistBtn').addEventListener('click', () => this.showPlaylistModal());
        document.getElementById('selectAllVideosBtn').addEventListener('click', () => this.selectAllVideos());
        document.getElementById('clearAllVideosBtn').addEventListener('click', () => this.clearAllVideos());
        document.getElementById('generatePlaylistConfirmBtn').addEventListener('click', () => this.generatePlaylist());
        document.getElementById('copyPlaylistBtn').addEventListener('click', () => this.copyPlaylist());

        // 下载模态框按钮
        document.getElementById('copyLinkBtn').addEventListener('click', () => this.copyDownloadLink());
        document.getElementById('openLinkBtn').addEventListener('click', () => this.openDownloadLink());
    }

    async connectAPI() {
        const token = document.getElementById('tokenInput').value.trim();
        if (!token) {
            this.showAlert('请输入 Token', 'warning');
            return;
        }

        const connectBtn = document.getElementById('connectBtn');
        connectBtn.disabled = true;
        connectBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> 连接中...';
        this.updateStatus('正在连接...');

        try {
            const response = await fetch('/api/connect', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ token: token })
            });

            const result = await response.json();
            
            if (result.success) {
                this.isConnected = true;
                this.currentFolderId = result.current_folder_id;
                this.currentPath = result.current_path;
                
                this.showMainContent();
                this.displayFiles(result.files);
                this.updateStatus('连接成功');
                this.showAlert('连接成功！', 'success');
            } else {
                this.showAlert(result.message, 'danger');
                this.updateStatus('连接失败: ' + result.message);
            }
        } catch (error) {
            this.showAlert('连接异常: ' + error.message, 'danger');
            this.updateStatus('连接异常: ' + error.message);
        } finally {
            connectBtn.disabled = false;
            connectBtn.innerHTML = '<i class="bi bi-plug"></i> 连接';
        }
    }

    showMainContent() {
        document.getElementById('tokenSection').style.display = 'none';
        document.getElementById('mainContent').style.display = 'block';
        document.getElementById('refreshBtn').disabled = false;
    }

    displayFiles(files) {
        const fileList = document.getElementById('fileList');
        fileList.innerHTML = '';

        if (files.length === 0) {
            fileList.innerHTML = `
                <tr>
                    <td colspan="4" class="text-center text-muted py-4">
                        <i class="bi bi-folder-x" style="font-size: 2em;"></i>
                        <p class="mt-2 mb-0">文件夹为空</p>
                    </td>
                </tr>
            `;
            return;
        }

        files.forEach(file => {
            const row = document.createElement('tr');
            row.className = 'file-list-item';
            row.dataset.fid = file.fid;
            row.dataset.id = file.id;
            row.dataset.isFolder = file.is_folder;
            row.dataset.fileName = file.name;

            const icon = file.is_folder ? 
                '<i class="bi bi-folder-fill file-icon folder-icon"></i>' : 
                '<i class="bi bi-file-earmark file-icon file-icon-default"></i>';

            const size = file.is_folder ? '-' : file.size_str;
            const time = this.formatTime(file.create_time);

            row.innerHTML = `
                <td>
                    ${icon}
                    <span>${file.name}</span>
                </td>
                <td class="file-size">${size}</td>
                <td class="file-time">${time}</td>
                <td>
                    ${file.is_folder ? 
                        '<button class="btn btn-outline-primary btn-sm" onclick="app.enterFolder(\'' + file.id + '\', \'' + file.name + '\')"><i class="bi bi-folder-open"></i> 打开</button>' :
                        '<button class="btn btn-outline-success btn-sm" onclick="app.selectFile(this)"><i class="bi bi-check-circle"></i> 选择</button>'
                    }
                </td>
            `;

            // 双击事件
            row.addEventListener('dblclick', () => {
                if (file.is_folder) {
                    this.enterFolder(file.id, file.name);
                } else {
                    this.selectFile(row);
                    this.getDownloadLink();
                }
            });

            fileList.appendChild(row);
        });

        this.updatePathBreadcrumb();
    }

    selectFile(element) {
        // 移除之前的选择
        document.querySelectorAll('.file-list-item').forEach(item => {
            item.classList.remove('selected');
        });

        // 选择当前文件
        const row = element.closest('tr');
        row.classList.add('selected');

        this.selectedFile = {
            fid: row.dataset.fid,
            id: row.dataset.id,
            name: row.dataset.fileName,
            isFolder: row.dataset.isFolder === 'true'
        };

        this.showFileInfo();
    }

    showFileInfo() {
        if (!this.selectedFile) return;

        const fileInfoCard = document.getElementById('fileInfoCard');
        const fileInfo = document.getElementById('fileInfo');

        fileInfo.innerHTML = `
            <p><strong>文件名:</strong> ${this.selectedFile.name}</p>
            <p><strong>类型:</strong> ${this.selectedFile.isFolder ? '文件夹' : '文件'}</p>
            <p><strong>ID:</strong> ${this.selectedFile.fid}</p>
        `;

        fileInfoCard.style.display = 'block';
    }

    async enterFolder(folderId, folderName) {
        this.updateStatus(`正在加载文件夹: ${folderName}`);

        try {
            const response = await fetch(`/api/browse/${folderId}`);
            const result = await response.json();

            if (result.success) {
                // 保存历史
                this.folderHistory.push({
                    id: this.currentFolderId,
                    name: this.currentPath
                });

                this.currentFolderId = folderId;
                this.currentPath = this.currentPath === '根目录' ? folderName : `${this.currentPath}/${folderName}`;

                this.displayFiles(result.files);
                document.getElementById('backBtn').disabled = false;
                this.updateStatus(`已加载 ${result.files.length} 个项目`);
            } else {
                this.showAlert(result.message, 'danger');
                this.updateStatus('加载失败: ' + result.message);
            }
        } catch (error) {
            this.showAlert('加载异常: ' + error.message, 'danger');
            this.updateStatus('加载异常: ' + error.message);
        }
    }

    goBack() {
        if (this.folderHistory.length === 0) return;

        const lastFolder = this.folderHistory.pop();
        this.currentFolderId = lastFolder.id;
        this.currentPath = lastFolder.name;

        if (this.folderHistory.length === 0) {
            document.getElementById('backBtn').disabled = true;
        }

        this.refreshCurrentFolder();
    }

    async refreshCurrentFolder() {
        console.log('refreshCurrentFolder 被调用');
        console.log('isConnected:', this.isConnected);
        console.log('currentFolderId:', this.currentFolderId);

        if (!this.isConnected) {
            console.log('未连接，跳过刷新');
            return;
        }

        this.updateStatus('正在刷新...');

        try {
            console.log(`发送刷新请求: /api/browse/${this.currentFolderId}`);
            const response = await fetch(`/api/browse/${this.currentFolderId}`);
            const result = await response.json();
            console.log('刷新响应:', result);

            if (result.success) {
                console.log(`刷新成功，文件数量: ${result.files.length}`);
                this.displayFiles(result.files);
                this.updateStatus(`已刷新，共 ${result.files.length} 个项目`);
            } else {
                console.log('刷新失败:', result.message);
                this.showAlert(result.message, 'danger');
                this.updateStatus('刷新失败: ' + result.message);
            }
        } catch (error) {
            console.error('刷新异常:', error);
            this.showAlert('刷新异常: ' + error.message, 'danger');
            this.updateStatus('刷新异常: ' + error.message);
        }
    }

    async getDownloadLink() {
        if (!this.selectedFile || this.selectedFile.isFolder) {
            this.showAlert('请选择一个文件', 'warning');
            return;
        }

        this.updateStatus(`正在获取下载链接: ${this.selectedFile.name}`);

        try {
            const response = await fetch(`/api/download/${this.selectedFile.fid}`);
            const result = await response.json();

            if (result.success) {
                this.showDownloadModal(this.selectedFile.name, result.download_url);
                this.updateStatus(`已获取下载链接: ${this.selectedFile.name}`);
            } else {
                this.showAlert(result.message, 'danger');
                this.updateStatus('获取失败: ' + result.message);
            }
        } catch (error) {
            this.showAlert('获取异常: ' + error.message, 'danger');
            this.updateStatus('获取异常: ' + error.message);
        }
    }

    showDownloadModal(fileName, downloadUrl) {
        document.getElementById('downloadFileName').textContent = fileName;
        document.getElementById('downloadUrl').value = downloadUrl;
        
        const modal = new bootstrap.Modal(document.getElementById('downloadModal'));
        modal.show();
    }

    copyDownloadLink() {
        const downloadUrl = document.getElementById('downloadUrl');
        downloadUrl.select();
        document.execCommand('copy');
        this.showAlert('下载链接已复制到剪贴板', 'success');
    }

    openDownloadLink() {
        const downloadUrl = document.getElementById('downloadUrl').value;
        window.open(downloadUrl, '_blank');
    }

    async handleDragDropItems(items) {
        const files = [];

        for (let i = 0; i < items.length; i++) {
            const item = items[i];
            if (item.kind === 'file') {
                const entry = item.webkitGetAsEntry();
                if (entry) {
                    await this.traverseFileTree(entry, files);
                }
            }
        }

        if (files.length > 0) {
            this.handleFileSelect(files, 'mixed');
        }
    }

    async traverseFileTree(item, files, path = '') {
        return new Promise((resolve) => {
            if (item.isFile) {
                item.file((file) => {
                    // 保存文件的相对路径信息
                    file.relativePath = path + file.name;
                    files.push(file);
                    resolve();
                });
            } else if (item.isDirectory) {
                const dirReader = item.createReader();
                dirReader.readEntries(async (entries) => {
                    for (let entry of entries) {
                        await this.traverseFileTree(entry, files, path + item.name + '/');
                    }
                    resolve();
                });
            }
        });
    }

    async handleFileSelect(files, type = 'files') {
        if (files.length === 0) return;

        const progressContainer = document.getElementById('progressContainer');
        const progressBar = document.getElementById('progressBar');
        const progressText = document.getElementById('progressText');

        progressContainer.style.display = 'block';
        progressBar.style.width = '0%';
        progressText.textContent = '准备上传...';

        // 显示文件信息
        const fileArray = Array.from(files);
        const totalSize = fileArray.reduce((sum, f) => sum + f.size, 0);
        const sizeStr = this.formatFileSize(totalSize);

        let statusMessage = '';
        if (type === 'folder') {
            statusMessage = `准备上传文件夹 (${files.length} 个文件, ${sizeStr})`;
        } else if (type === 'mixed') {
            statusMessage = `准备上传 ${files.length} 个文件/文件夹 (${sizeStr})`;
        } else {
            const fileNames = fileArray.slice(0, 3).map(f => f.name).join(', ');
            const moreText = files.length > 3 ? ` 等${files.length}个文件` : '';
            statusMessage = `准备上传 ${files.length} 个文件 (${sizeStr}): ${fileNames}${moreText}`;
        }

        this.updateStatus(statusMessage);

        // 如果是多文件上传，使用批量上传
        if (files.length > 1) {
            await this.handleMultipleFileUpload(fileArray);
        } else {
            await this.handleSingleFileUpload(fileArray[0]);
        }

        // 清空文件输入
        document.getElementById('fileInput').value = '';
        document.getElementById('folderInput').value = '';
    }

    async handleSingleFileUpload(file) {
        const progressContainer = document.getElementById('progressContainer');
        const progressBar = document.getElementById('progressBar');
        const progressText = document.getElementById('progressText');

        const formData = new FormData();
        formData.append('files', file);
        formData.append('folder_id', this.currentFolderId);

        try {
            progressText.textContent = '正在上传...';
            progressBar.style.width = '10%';

            console.log('开始上传文件到文件夹:', this.currentFolderId);

            // 使用XMLHttpRequest来支持进度监控
            const xhr = new XMLHttpRequest();

            // 监听上传进度
            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable) {
                    const percentComplete = (e.loaded / e.total) * 100;
                    progressBar.style.width = percentComplete + '%';
                    progressText.textContent = `上传中... ${Math.round(percentComplete)}%`;
                    console.log(`上传进度: ${Math.round(percentComplete)}%`);
                }
            });

            // 监听完成事件
            xhr.addEventListener('load', () => {
                console.log('上传响应状态:', xhr.status);

                if (xhr.status === 200) {
                    try {
                        console.log('服务器响应状态:', xhr.status);
                        console.log('服务器响应内容:', xhr.responseText);
                        console.log('响应内容类型:', xhr.getResponseHeader('Content-Type'));

                        if (!xhr.responseText) {
                            throw new Error('服务器返回空响应');
                        }

                        const result = JSON.parse(xhr.responseText);
                        console.log('解析后的上传结果:', result);

                        if (result.success) {
                            progressBar.style.width = '100%';
                            progressText.textContent = result.message;
                            this.showAlert(result.message, 'success');
                            this.updateStatus(result.message);

                            console.log('上传成功，准备刷新文件列表...');

                            // 刷新文件列表
                            setTimeout(() => {
                                console.log('开始刷新文件列表...');
                                this.refreshCurrentFolder();
                                progressContainer.style.display = 'none';
                                console.log('文件列表刷新完成');
                            }, 2000);
                        } else {
                            console.log('上传失败:', result.message);
                            this.showAlert(result.message, 'danger');
                            this.updateStatus('上传失败: ' + result.message);
                            progressContainer.style.display = 'none';
                        }
                    } catch (e) {
                        console.error('解析响应失败:', e);
                        console.error('原始响应:', xhr.responseText);
                        this.showAlert('服务器响应格式错误', 'danger');
                        progressContainer.style.display = 'none';
                    }
                } else {
                    this.showAlert(`上传失败: HTTP ${xhr.status}`, 'danger');
                    progressContainer.style.display = 'none';
                }
            });

            // 监听错误事件
            xhr.addEventListener('error', () => {
                console.error('上传请求失败');
                this.showAlert('网络错误，上传失败', 'danger');
                this.updateStatus('网络错误，上传失败');
                progressContainer.style.display = 'none';
            });

            // 发送请求
            xhr.open('POST', '/api/upload');
            xhr.send(formData);

        } catch (error) {
            console.error('上传错误:', error);
            this.showAlert('上传异常: ' + error.message, 'danger');
            this.updateStatus('上传异常: ' + error.message);
            progressContainer.style.display = 'none';
        }

        // 清空文件输入
        document.getElementById('fileInput').value = '';
        document.getElementById('folderInput').value = '';
    }

    async handleMultipleFileUpload(files) {
        const progressContainer = document.getElementById('progressContainer');
        const progressBar = document.getElementById('progressBar');
        const progressText = document.getElementById('progressText');

        let uploadedCount = 0;
        let failedCount = 0;
        const totalFiles = files.length;

        progressText.textContent = `上传中... 0/${totalFiles}`;

        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            const progress = ((i) / totalFiles) * 100;

            progressBar.style.width = progress + '%';
            progressText.textContent = `上传中... ${i}/${totalFiles} - ${file.name}`;

            console.log(`上传文件 ${i + 1}/${totalFiles}: ${file.name}`);

            try {
                const success = await this.uploadSingleFile(file);
                if (success) {
                    uploadedCount++;
                    console.log(`✅ 文件 ${file.name} 上传成功`);
                } else {
                    failedCount++;
                    console.log(`❌ 文件 ${file.name} 上传失败`);
                }
            } catch (error) {
                failedCount++;
                console.error(`❌ 文件 ${file.name} 上传异常:`, error);
            }

            // 更新进度
            const currentProgress = ((i + 1) / totalFiles) * 100;
            progressBar.style.width = currentProgress + '%';
        }

        // 上传完成
        progressBar.style.width = '100%';
        const resultMessage = `上传完成: 成功 ${uploadedCount}/${totalFiles}`;
        progressText.textContent = resultMessage;

        if (uploadedCount > 0) {
            this.showAlert(resultMessage, uploadedCount === totalFiles ? 'success' : 'warning');
            this.updateStatus(resultMessage);

            // 刷新文件列表
            setTimeout(() => {
                console.log('批量上传完成，刷新文件列表...');
                this.refreshCurrentFolder();
                progressContainer.style.display = 'none';
            }, 2000);
        } else {
            this.showAlert('所有文件上传失败', 'danger');
            this.updateStatus('所有文件上传失败');
            progressContainer.style.display = 'none';
        }
    }

    async uploadSingleFile(file) {
        return new Promise((resolve) => {
            const formData = new FormData();
            formData.append('files', file);
            formData.append('folder_id', this.currentFolderId);

            const xhr = new XMLHttpRequest();

            xhr.addEventListener('load', () => {
                if (xhr.status === 200) {
                    try {
                        const result = JSON.parse(xhr.responseText);
                        resolve(result.success);
                    } catch (e) {
                        console.error('解析响应失败:', e);
                        resolve(false);
                    }
                } else {
                    resolve(false);
                }
            });

            xhr.addEventListener('error', () => {
                resolve(false);
            });

            xhr.open('POST', '/api/upload');
            xhr.send(formData);
        });
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    async deleteFile() {
        if (!this.selectedFile) {
            this.showAlert('请选择要删除的文件', 'warning');
            return;
        }

        if (!confirm(`确定要删除 "${this.selectedFile.name}" 吗？`)) {
            return;
        }

        this.updateStatus(`正在删除: ${this.selectedFile.name}`);

        try {
            const response = await fetch('/api/delete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    file_id: this.selectedFile.id,
                    is_folder: this.selectedFile.isFolder
                })
            });

            const result = await response.json();

            if (result.success) {
                this.showAlert('删除成功', 'success');
                this.updateStatus('删除成功');

                // 清除选择并刷新列表
                this.selectedFile = null;
                document.getElementById('fileInfoCard').style.display = 'none';
                this.refreshCurrentFolder();
            } else {
                this.showAlert(result.message, 'danger');
                this.updateStatus('删除失败: ' + result.message);
            }
        } catch (error) {
            this.showAlert('删除异常: ' + error.message, 'danger');
            this.updateStatus('删除异常: ' + error.message);
        }
    }

    showCreateFolderModal() {
        document.getElementById('folderNameInput').value = '';
        const modal = new bootstrap.Modal(document.getElementById('createFolderModal'));
        modal.show();

        // 聚焦到输入框
        setTimeout(() => {
            document.getElementById('folderNameInput').focus();
        }, 500);
    }

    async createFolder() {
        const folderName = document.getElementById('folderNameInput').value.trim();
        if (!folderName) {
            this.showAlert('请输入文件夹名称', 'warning');
            return;
        }

        this.updateStatus(`正在创建文件夹: ${folderName}`);

        try {
            const response = await fetch('/api/create_folder', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    folder_name: folderName,
                    parent_id: this.currentFolderId
                })
            });

            const result = await response.json();

            if (result.success) {
                this.showAlert('文件夹创建成功', 'success');
                this.updateStatus('文件夹创建成功');

                // 关闭模态框
                const modal = bootstrap.Modal.getInstance(document.getElementById('createFolderModal'));
                modal.hide();

                // 刷新文件列表
                this.refreshCurrentFolder();
            } else {
                this.showAlert(result.message, 'danger');
                this.updateStatus('创建失败: ' + result.message);
            }
        } catch (error) {
            this.showAlert('创建异常: ' + error.message, 'danger');
            this.updateStatus('创建异常: ' + error.message);
        }
    }

    showPlaylistModal() {
        // 获取当前文件夹中的视频文件
        const videoFiles = this.getVideoFiles();

        if (videoFiles.length === 0) {
            this.showAlert('当前文件夹中没有视频文件', 'warning');
            return;
        }

        this.displayVideoFilesList(videoFiles);
        const modal = new bootstrap.Modal(document.getElementById('playlistModal'));
        modal.show();
    }

    getVideoFiles() {
        // 从当前显示的文件列表中筛选视频文件
        const videoExtensions = ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp', '.ts', '.m3u8'];
        const fileRows = document.querySelectorAll('#fileList tr');
        const videoFiles = [];

        fileRows.forEach(row => {
            const isFolder = row.dataset.isFolder === 'true';
            if (!isFolder) {
                const fileName = row.dataset.fileName;
                const fileExt = fileName.toLowerCase().substring(fileName.lastIndexOf('.'));

                if (videoExtensions.includes(fileExt)) {
                    videoFiles.push({
                        fid: row.dataset.fid,
                        id: row.dataset.id,
                        name: fileName
                    });
                }
            }
        });

        // 按文件名排序
        videoFiles.sort((a, b) => a.name.localeCompare(b.name));
        return videoFiles;
    }

    displayVideoFilesList(videoFiles) {
        const container = document.getElementById('videoFilesList');
        container.innerHTML = '';

        if (videoFiles.length === 0) {
            container.innerHTML = '<p class="text-muted text-center">没有找到视频文件</p>';
            return;
        }

        videoFiles.forEach((file, index) => {
            const div = document.createElement('div');
            div.className = 'form-check mb-2';
            div.innerHTML = `
                <input class="form-check-input video-file-checkbox" type="checkbox" value="${index}" id="video_${index}">
                <label class="form-check-label" for="video_${index}">
                    <i class="bi bi-play-circle text-primary me-2"></i>
                    ${file.name}
                </label>
            `;
            container.appendChild(div);
        });

        // 存储视频文件列表供后续使用
        this.currentVideoFiles = videoFiles;
    }

    selectAllVideos() {
        const checkboxes = document.querySelectorAll('.video-file-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.checked = true;
        });
    }

    clearAllVideos() {
        const checkboxes = document.querySelectorAll('.video-file-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.checked = false;
        });
    }

    async generatePlaylist() {
        const checkboxes = document.querySelectorAll('.video-file-checkbox:checked');

        if (checkboxes.length === 0) {
            this.showAlert('请选择至少一个视频文件', 'warning');
            return;
        }

        const folderPath = document.getElementById('folderPathInput').value.trim();
        if (!folderPath) {
            this.showAlert('请输入文件夹路径', 'warning');
            return;
        }

        const selectedFiles = [];
        checkboxes.forEach(checkbox => {
            const index = parseInt(checkbox.value);
            selectedFiles.push(this.currentVideoFiles[index]);
        });

        this.updateStatus(`正在生成播放列表，共 ${selectedFiles.length} 个文件...`);

        try {
            const response = await fetch('/api/generate_playlist', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    file_ids: selectedFiles,
                    folder_path: folderPath
                })
            });

            const result = await response.json();

            if (result.success) {
                this.showPlaylistResult(result);
                this.updateStatus(`播放列表生成成功: ${result.success_count}/${result.total_files}`);

                // 关闭选择模态框
                const selectModal = bootstrap.Modal.getInstance(document.getElementById('playlistModal'));
                selectModal.hide();
            } else {
                this.showAlert(result.message, 'danger');
                this.updateStatus('播放列表生成失败: ' + result.message);
            }
        } catch (error) {
            this.showAlert('生成播放列表异常: ' + error.message, 'danger');
            this.updateStatus('生成播放列表异常: ' + error.message);
        }
    }

    showPlaylistResult(result) {
        document.getElementById('playlistResult').value = result.playlist;

        let statsHtml = `
            <div class="alert alert-success">
                <strong>生成成功!</strong>
                共处理 ${result.total_files} 个文件，成功生成 ${result.success_count} 个播放链接
            </div>
        `;

        if (result.failed_files && result.failed_files.length > 0) {
            statsHtml += `
                <div class="alert alert-warning">
                    <strong>部分文件处理失败:</strong>
                    <ul class="mb-0 mt-2">
                        ${result.failed_files.map(file => `<li>${file}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        document.getElementById('playlistStats').innerHTML = statsHtml;

        const modal = new bootstrap.Modal(document.getElementById('playlistResultModal'));
        modal.show();
    }

    copyPlaylist() {
        const playlistText = document.getElementById('playlistResult');
        playlistText.select();
        document.execCommand('copy');
        this.showAlert('播放列表已复制到剪贴板', 'success');
    }

    updatePathBreadcrumb() {
        const breadcrumb = document.getElementById('pathBreadcrumb');
        const pathParts = this.currentPath.split('/');
        
        breadcrumb.innerHTML = '';
        
        pathParts.forEach((part, index) => {
            const li = document.createElement('li');
            li.className = 'breadcrumb-item';
            
            if (index === pathParts.length - 1) {
                li.className += ' active';
                li.textContent = part;
            } else {
                const a = document.createElement('a');
                a.href = '#';
                a.textContent = part;
                a.addEventListener('click', (e) => {
                    e.preventDefault();
                    // TODO: 实现面包屑导航
                });
                li.appendChild(a);
            }
            
            breadcrumb.appendChild(li);
        });
    }

    formatTime(timeStr) {
        if (!timeStr || timeStr.length !== 14) return '';
        
        try {
            const year = timeStr.substr(0, 4);
            const month = timeStr.substr(4, 2);
            const day = timeStr.substr(6, 2);
            const hour = timeStr.substr(8, 2);
            const minute = timeStr.substr(10, 2);
            
            return `${year}-${month}-${day} ${hour}:${minute}`;
        } catch (error) {
            return timeStr;
        }
    }

    updateStatus(message) {
        document.getElementById('statusText').textContent = message;
    }

    showAlert(message, type = 'info') {
        // 创建 Bootstrap 警告框
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alertDiv);
        
        // 3秒后自动消失
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 3000);
    }
}

// 初始化应用
const app = new WoPanWeb();

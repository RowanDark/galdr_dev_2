// interceptor/gui/src/main/main.ts
import { app, BrowserWindow, ipcMain, Menu } from 'electron';
import * as path from 'path';

class InterceptorGUI {
  private mainWindow: BrowserWindow | null = null;
  private isDev = process.env.NODE_ENV === 'development';

  constructor() {
    this.initializeApp();
  }

  private initializeApp() {
    app.whenReady().then(() => {
      this.createMainWindow();
      this.setupMenu();
      this.setupIPC();
    });

    app.on('window-all-closed', () => {
      if (process.platform !== 'darwin') {
        app.quit();
      }
    });

    app.on('activate', () => {
      if (BrowserWindow.getAllWindows().length === 0) {
        this.createMainWindow();
      }
    });
  }

  private createMainWindow() {
    this.mainWindow = new BrowserWindow({
      width: 1400,
      height: 900,
      minWidth: 1200,
      minHeight: 700,
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true,
        preload: path.join(__dirname, 'preload.js')
      },
      titleBarStyle: 'hiddenInset',
      show: false
    });

    const startUrl = this.isDev 
      ? 'http://localhost:3000' 
      : `file://${path.join(__dirname, '../renderer/index.html')}`;

    this.mainWindow.loadURL(startUrl);

    this.mainWindow.once('ready-to-show', () => {
      this.mainWindow?.show();
    });

    if (this.isDev) {
      this.mainWindow.webContents.openDevTools();
    }
  }

  private setupMenu() {
    const template = [
      {
        label: 'File',
        submenu: [
          {
            label: 'New Project',
            accelerator: 'CmdOrCtrl+N',
            click: () => this.mainWindow?.webContents.send('menu-new-project')
          },
          {
            label: 'Import Traffic',
            accelerator: 'CmdOrCtrl+I',
            click: () => this.mainWindow?.webContents.send('menu-import-traffic')
          },
          { type: 'separator' },
          {
            label: 'Exit',
            accelerator: process.platform === 'darwin' ? 'Cmd+Q' : 'Ctrl+Q',
            click: () => app.quit()
          }
        ]
      },
      {
        label: 'Proxy',
        submenu: [
          {
            label: 'Start Proxy',
            accelerator: 'CmdOrCtrl+R',
            click: () => this.mainWindow?.webContents.send('menu-start-proxy')
          },
          {
            label: 'Stop Proxy',
            accelerator: 'CmdOrCtrl+S',
            click: () => this.mainWindow?.webContents.send('menu-stop-proxy')
          },
          { type: 'separator' },
          {
            label: 'Clear History',
            accelerator: 'CmdOrCtrl+L',
            click: () => this.mainWindow?.webContents.send('menu-clear-history')
          }
        ]
      }
    ];

    const menu = Menu.buildFromTemplate(template as any);
    Menu.setApplicationMenu(menu);
  }

  private setupIPC() {
    ipcMain.handle('get-app-version', () => {
      return app.getVersion();
    });

    ipcMain.handle('show-save-dialog', async () => {
      const { dialog } = await import('electron');
      return dialog.showSaveDialog(this.mainWindow!);
    });
  }
}

new InterceptorGUI();

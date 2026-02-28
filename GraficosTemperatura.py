import os
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import filedialog, messagebox

class AplicativoGraficos(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Visualizador de Gráficos b4cast")
        self.geometry("1100x650") 
        self.minsize(850, 500) 
        
        # Variáveis para armazenar estado
        self.arquivos_encontrados = []
        self.arquivo_atual = None
        self.canvas_grafico = None
        self.entries_legendas = [] 

        # --- EVENTOS GLOBAIS DE TECLADO ---
        self.bind('<Up>', self.navegar_arquivos)
        self.bind('<Down>', self.navegar_arquivos)

        # --- CONSTRUÇÃO DA INTERFACE ---
        
        # Frame Esquerdo Principal (LARGURA AUMENTADA PARA 370 PARA CABER LADO A LADO)
        self.frame_esquerdo = tk.Frame(self, width=370, bg="#f0f0f0")
        self.frame_esquerdo.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        self.frame_esquerdo.pack_propagate(False) 

        # Botão de selecionar pasta
        self.btn_selecionar = tk.Button(
            self.frame_esquerdo, 
            text="Selecionar Pasta do Projeto", 
            command=self.selecionar_pasta,
            font=("Arial", 10, "bold"),
            bg="#00529b", fg="white",
            relief=tk.FLAT, pady=5
        )
        self.btn_selecionar.pack(fill=tk.X, pady=(0, 10))

        # Lista de arquivos com Scrollbar
        self.frame_lista = tk.Frame(self.frame_esquerdo)
        self.frame_lista.pack(fill=tk.X, pady=(0, 10))
        
        self.scroll_lista = tk.Scrollbar(self.frame_lista)
        self.scroll_lista.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.lista_arquivos = tk.Listbox(
            self.frame_lista, 
            yscrollcommand=self.scroll_lista.set,
            font=("Arial", 10),
            selectbackground="#00529b",
            height=8 
        )
        self.lista_arquivos.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scroll_lista.config(command=self.lista_arquivos.yview)
        self.lista_arquivos.bind('<<ListboxSelect>>', self.ao_selecionar_arquivo)


        # --- ÁREA ROLÁVEL PARA OS CONTROLES ---
        self.container_controles = tk.Frame(self.frame_esquerdo, bg="#f0f0f0")
        self.container_controles.pack(fill=tk.BOTH, expand=True)

        self.canvas_controles = tk.Canvas(self.container_controles, bg="#f0f0f0", highlightthickness=0)
        self.scrollbar_controles = tk.Scrollbar(self.container_controles, orient="vertical", command=self.canvas_controles.yview)
        
        self.scrollable_frame = tk.Frame(self.canvas_controles, bg="#f0f0f0")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas_controles.configure(scrollregion=self.canvas_controles.bbox("all"))
        )

        self.canvas_window = self.canvas_controles.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas_controles.configure(yscrollcommand=self.scrollbar_controles.set)

        self.canvas_controles.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar_controles.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas_controles.bind('<Configure>', lambda e: self.canvas_controles.itemconfig(self.canvas_window, width=e.width))

        def _on_mousewheel(event):
            self.canvas_controles.yview_scroll(int(-1*(event.delta/120)), "units")
        
        self.canvas_controles.bind("<Enter>", lambda _: self.canvas_controles.bind_all("<MouseWheel>", _on_mousewheel))
        self.canvas_controles.bind("<Leave>", lambda _: self.canvas_controles.unbind_all("<MouseWheel>"))


        # --- CONTROLES DENTRO DA ÁREA ROLÁVEL ---
        
        # CONTROLE DE TÍTULO
        self.frame_titulo = tk.LabelFrame(self.scrollable_frame, text="Título do Gráfico", bg="#f0f0f0", font=("Arial", 9, "bold"))
        self.frame_titulo.pack(fill=tk.X, pady=(0, 5), ipadx=5, ipady=5)
        
        self.entry_titulo = tk.Entry(self.frame_titulo)
        self.entry_titulo.pack(fill=tk.X, padx=5, pady=5)
        tk.Label(self.frame_titulo, text="Deixe em branco para o padrão automático.", bg="#f0f0f0", fg="gray", font=("Arial", 8, "italic")).pack(pady=(0,2))


        # --- NOVO: CONTAINER PARA EIXOS LADO A LADO ---
        self.container_eixos = tk.Frame(self.scrollable_frame, bg="#f0f0f0")
        self.container_eixos.pack(fill=tk.X, pady=5)

        # CONTROLES DO EIXO Y (Esquerda)
        self.frame_controles = tk.LabelFrame(self.container_eixos, text="Eixo Y (Ordenadas)", bg="#f0f0f0", font=("Arial", 9, "bold"))
        self.frame_controles.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 2), ipadx=2, ipady=2)

        tk.Label(self.frame_controles, text="Inicial:", bg="#f0f0f0").grid(row=0, column=0, sticky="e", padx=2, pady=5)
        self.entry_ymin = tk.Entry(self.frame_controles, width=8)
        self.entry_ymin.grid(row=0, column=1, sticky="w", padx=2, pady=5)

        tk.Label(self.frame_controles, text="Final:", bg="#f0f0f0").grid(row=1, column=0, sticky="e", padx=2, pady=5)
        self.entry_ymax = tk.Entry(self.frame_controles, width=8)
        self.entry_ymax.grid(row=1, column=1, sticky="w", padx=2, pady=5)

        tk.Label(self.frame_controles, text="Amplitude:", bg="#f0f0f0").grid(row=2, column=0, sticky="e", padx=2, pady=5)
        self.entry_ystep = tk.Entry(self.frame_controles, width=8)
        self.entry_ystep.grid(row=2, column=1, sticky="w", padx=2, pady=5)

        # CONTROLES DO EIXO X (Direita)
        self.frame_controles_x = tk.LabelFrame(self.container_eixos, text="Eixo X (Abscissas)", bg="#f0f0f0", font=("Arial", 9, "bold"))
        self.frame_controles_x.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(2, 0), ipadx=2, ipady=2)

        tk.Label(self.frame_controles_x, text="Inicial:", bg="#f0f0f0").grid(row=0, column=0, sticky="e", padx=2, pady=5)
        self.entry_xmin = tk.Entry(self.frame_controles_x, width=8)
        self.entry_xmin.grid(row=0, column=1, sticky="w", padx=2, pady=5)

        tk.Label(self.frame_controles_x, text="Final:", bg="#f0f0f0").grid(row=1, column=0, sticky="e", padx=2, pady=5)
        self.entry_xmax = tk.Entry(self.frame_controles_x, width=8)
        self.entry_xmax.grid(row=1, column=1, sticky="w", padx=2, pady=5)

        tk.Label(self.frame_controles_x, text="Amplitude:", bg="#f0f0f0").grid(row=2, column=0, sticky="e", padx=2, pady=5)
        self.entry_xstep = tk.Entry(self.frame_controles_x, width=8)
        self.entry_xstep.grid(row=2, column=1, sticky="w", padx=2, pady=5)

        # Aviso unificado para os dois eixos
        tk.Label(self.scrollable_frame, text="Deixe em branco para o modo automático nos eixos.", bg="#f0f0f0", fg="gray", font=("Arial", 8, "italic")).pack(pady=(0,5))


        # CONTROLES DA LEGENDA
        self.frame_legenda = tk.LabelFrame(self.scrollable_frame, text="Configurações da Legenda", bg="#f0f0f0", font=("Arial", 9, "bold"))
        self.frame_legenda.pack(fill=tk.X, pady=5, ipadx=5, ipady=5)

        self.var_mostrar_legenda = tk.BooleanVar(value=False)
        self.chk_mostrar_legenda = tk.Checkbutton(
            self.frame_legenda, text="Mostrar Legenda no Gráfico", 
            variable=self.var_mostrar_legenda, bg="#f0f0f0"
        )
        self.chk_mostrar_legenda.pack(anchor="w", padx=5, pady=(0, 5))

        self.frame_nomes_series = tk.Frame(self.frame_legenda, bg="#f0f0f0")
        self.frame_nomes_series.pack(fill=tk.X, padx=5)

        # Botões
        self.btn_aplicar = tk.Button(
            self.scrollable_frame, 
            text="Aplicar Alterações ao Gráfico", 
            command=self.atualizar_grafico_atual,
            font=("Arial", 9, "bold"),
            bg="#e0e0e0",
            pady=5
        )
        self.btn_aplicar.pack(fill=tk.X, pady=(10, 5))

        self.btn_salvar = tk.Button(
            self.scrollable_frame, 
            text="💾 Salvar Gráfico (PNG)", 
            command=self.salvar_grafico,
            font=("Arial", 10, "bold"),
            bg="#28a745", fg="white", 
            relief=tk.FLAT, pady=8
        )
        self.btn_salvar.pack(fill=tk.X, pady=(5, 5))
        
        # BOTÃO DE COPIAR (ÁREA DE TRANSFERÊNCIA)
        self.btn_copiar = tk.Button(
            self.scrollable_frame, 
            text="📋 Copiar Gráfico", 
            command=self.copiar_grafico,
            font=("Arial", 10, "bold"),
            bg="#17a2b8", fg="white", 
            relief=tk.FLAT, pady=8
        )
        self.btn_copiar.pack(fill=tk.X, pady=(0, 10))


        # --- Frame Direito (Gráfico) ---
        self.frame_direito = tk.Frame(self, bg="white", relief=tk.SUNKEN, borderwidth=1)
        self.frame_direito.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(0, 10), pady=10)
        
        self.label_aviso = tk.Label(
            self.frame_direito, 
            text="Selecione uma pasta para carregar os arquivos.\nDepois, clique em um arquivo na lista para ver o gráfico.", 
            bg="white", font=("Arial", 12)
        )
        self.label_aviso.pack(expand=True)

    def navegar_arquivos(self, event):
        if isinstance(self.focus_get(), tk.Entry):
            return

        if not self.arquivos_encontrados:
            return
            
        selecao = self.lista_arquivos.curselection()
        if not selecao:
            novo_idx = 0
        else:
            idx = selecao[0]
            if event.keysym == 'Up':
                novo_idx = max(0, idx - 1)
            elif event.keysym == 'Down':
                novo_idx = min(len(self.arquivos_encontrados) - 1, idx + 1)
            else:
                return

        self.lista_arquivos.selection_clear(0, tk.END)
        self.lista_arquivos.selection_set(novo_idx)
        self.lista_arquivos.activate(novo_idx)
        self.lista_arquivos.see(novo_idx) 
        
        self.ao_selecionar_arquivo(None)
        
        return "break"

    def selecionar_pasta(self):
        pasta = filedialog.askdirectory(title="Selecione a pasta com os CSVs do b4cast")
        if not pasta:
            return

        self.arquivos_encontrados = []
        self.lista_arquivos.delete(0, tk.END)

        for raiz, _, arquivos in os.walk(pasta):
            for arquivo in arquivos:
                if arquivo.lower().endswith('.csv'):
                    caminho_completo = os.path.join(raiz, arquivo)
                    self.arquivos_encontrados.append(caminho_completo)

        if not self.arquivos_encontrados:
            messagebox.showinfo("Aviso", "Nenhum arquivo .csv encontrado nessa pasta.")
            return

        def natural_sort_key(s):
            return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]
        
        self.arquivos_encontrados.sort(key=natural_sort_key)

        for caminho in self.arquivos_encontrados:
            arquivo = os.path.basename(caminho)
            self.lista_arquivos.insert(tk.END, arquivo) 

        self.label_aviso.config(text="Arquivos carregados!\nUse o mouse ou as setas (Cima/Baixo) para visualizar.")

    def ao_selecionar_arquivo(self, event=None):
        selecao = self.lista_arquivos.curselection()
        if not selecao:
            return
        
        indice = selecao[0]
        self.arquivo_atual = self.arquivos_encontrados[indice]
        self.gerar_e_mostrar_grafico(self.arquivo_atual, novo_arquivo=True)

    def atualizar_grafico_atual(self):
        if self.arquivo_atual:
            self.gerar_e_mostrar_grafico(self.arquivo_atual, novo_arquivo=False)
        else:
            messagebox.showinfo("Aviso", "Por favor, selecione um arquivo na lista primeiro.")

    def salvar_grafico(self):
        if not self.canvas_grafico:
            messagebox.showwarning("Aviso", "Não há nenhum gráfico na tela para salvar.")
            return

        nome_sugerido = os.path.basename(self.arquivo_atual).replace('.csv', '.png')
        caminho_salvar = filedialog.asksaveasfilename(
            defaultextension=".png",
            initialfile=nome_sugerido,
            title="Salvar Gráfico como Imagem",
            filetypes=[("Imagens PNG", "*.png"), ("Todos os Arquivos", "*.*")]
        )

        if caminho_salvar:
            try:
                self.canvas_grafico.figure.savefig(caminho_salvar, dpi=300, bbox_inches='tight')
                messagebox.showinfo("Sucesso", f"Gráfico salvo com sucesso em:\n{caminho_salvar}")
            except Exception as e:
                messagebox.showerror("Erro", f"Ocorreu um erro ao salvar a imagem:\n{e}")

    # --- LÓGICA DE CÓPIA PARA ÁREA DE TRANSFERÊNCIA ---
    def copiar_grafico(self):
        if not self.canvas_grafico:
            messagebox.showwarning("Aviso", "Não há nenhum gráfico na tela para copiar.")
            return

        try:
            from PIL import Image
            import io
            import ctypes
            from ctypes import wintypes
            import struct

            buf = io.BytesIO()
            self.canvas_grafico.figure.savefig(buf, format='png', dpi=300, bbox_inches='tight', transparent=False, facecolor='white')
            buf.seek(0)
            
            img = Image.open(buf)
            
            dpi = 300
            pixels_por_cm = dpi / 2.54
            
            largura_px = int(11.0 * pixels_por_cm)
            altura_px = int(7.0 * pixels_por_cm)
            
            filtro = getattr(Image, 'Resampling', Image).LANCZOS
            img = img.resize((largura_px, altura_px), filtro)
            
            output = io.BytesIO()
            img.convert("RGB").save(output, "BMP")
            bmp_data = bytearray(output.getvalue())
            
            ppm = int(dpi / 0.0254) 
            
            struct.pack_into('<i', bmp_data, 38, ppm)
            struct.pack_into('<i', bmp_data, 42, ppm)
            
            data = bytes(bmp_data[14:])
            
            output.close()
            buf.close()

            CF_DIB = 8
            GMEM_MOVEABLE = 0x0002

            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32

            user32.OpenClipboard.argtypes = [wintypes.HWND]
            user32.EmptyClipboard.argtypes = []
            user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
            user32.SetClipboardData.restype = wintypes.HANDLE
            user32.CloseClipboard.argtypes = []

            kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
            kernel32.GlobalAlloc.restype = wintypes.HANDLE
            kernel32.GlobalLock.argtypes = [wintypes.HANDLE]
            kernel32.GlobalLock.restype = wintypes.LPVOID
            kernel32.GlobalUnlock.argtypes = [wintypes.HANDLE]
            kernel32.GlobalUnlock.restype = wintypes.BOOL

            msvcrt = ctypes.cdll.msvcrt
            msvcrt.memcpy.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t]
            msvcrt.memcpy.restype = ctypes.c_void_p

            hCd = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
            if not hCd:
                raise Exception("Falha ao alocar memória no Windows.")

            ptr = kernel32.GlobalLock(hCd)
            if not ptr:
                raise Exception("Falha ao travar memória no Windows.")

            msvcrt.memcpy(ptr, data, len(data))
            kernel32.GlobalUnlock(hCd)

            user32.OpenClipboard(0)
            user32.EmptyClipboard()
            user32.SetClipboardData(CF_DIB, hCd)
            user32.CloseClipboard()

            texto_original = self.btn_copiar.cget("text")
            self.btn_copiar.config(text="✔️ Copiado (11x7 cm)!")
            self.after(1500, lambda: self.btn_copiar.config(text=texto_original))

        except ImportError:
            messagebox.showerror("Erro", "A biblioteca 'Pillow' não está instalada.\nNo terminal, digite: pip install pillow")
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro interno ao copiar o gráfico:\n{e}")

    # --- GERADOR DO GRÁFICO ---
    def gerar_e_mostrar_grafico(self, caminho_csv, novo_arquivo=False):
        if self.label_aviso.winfo_ismapped():
            self.label_aviso.pack_forget()

        try:
            with open(caminho_csv, 'r', encoding='utf-8', errors='ignore') as f:
                linhas = f.readlines()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao ler o arquivo:\n{e}")
            return

        inicio_dados = 0
        linha_nomes = 0
        for i, linha in enumerate(linhas):
            if '"[hours]";"[°C]"' in linha or '[hours]' in linha:
                linha_nomes = i - 1  
                inicio_dados = i + 1 
                break

        if inicio_dados == 0 or linha_nomes < 0:
            messagebox.showwarning("Aviso", "Formato de cabeçalho não reconhecido neste arquivo.")
            return

        nomes_brutos = linhas[linha_nomes].strip().split(';')
        nomes_colunas_csv = [nome.replace('"', '').strip() for nome in nomes_brutos if nome.strip()]

        try:
            df = pd.read_csv(
                caminho_csv, sep=';', skiprows=inicio_dados, decimal=',',
                encoding='utf-8', engine='python', header=None, na_values=['#N/A', 'NaN', '']
            )
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao processar dados:\n{e}")
            return

        df = df.dropna(axis=1, how='all')
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df = df.dropna(subset=[df.columns[0]])

        if df.empty or len(df.columns) < 2:
            messagebox.showwarning("Aviso", "Nenhum dado numérico válido encontrado.")
            return

        coluna_tempo = df.columns[0]
        colunas_temperatura = df.columns[1:]

        if novo_arquivo:
            for widget in self.frame_nomes_series.winfo_children():
                widget.destroy()
            self.entries_legendas = []

            for i in range(len(colunas_temperatura)):
                nome_original = nomes_colunas_csv[i+1] if (i+1) < len(nomes_colunas_csv) else f"Série {i+1}"
                
                frame_linha = tk.Frame(self.frame_nomes_series, bg="#f0f0f0")
                frame_linha.pack(fill=tk.X, pady=2)
                
                lbl = tk.Label(frame_linha, text=f"Curva {i+1}:", bg="#f0f0f0", width=8, anchor="w")
                lbl.pack(side=tk.LEFT)
                
                ent = tk.Entry(frame_linha)
                ent.insert(0, nome_original) 
                ent.pack(side=tk.LEFT, fill=tk.X, expand=True)
                
                self.entries_legendas.append(ent)

        nomes_para_plotar = []
        for ent in self.entries_legendas:
            nome_digitado = ent.get().strip()
            nomes_para_plotar.append(nome_digitado if nome_digitado else "Série Desconhecida")

        fig, ax = plt.subplots(figsize=(8, 5), constrained_layout=True)
        cores_linhas = plt.cm.tab10.colors

        for i, col in enumerate(colunas_temperatura):
            nome_serie = nomes_para_plotar[i] if i < len(nomes_para_plotar) else f"Série {i+1}"
            cor = cores_linhas[i % len(cores_linhas)] 
            ax.plot(df[coluna_tempo], df[col], linewidth=3.0, label=nome_serie, color=cor)

        limite_y = 65
        ax.axhline(y=limite_y, color='red', linestyle='--', linewidth=2.5)

        xmax = df[coluna_tempo].max()
        ax.text(xmax, limite_y, 'Limite', color='red', fontsize=22, fontweight='bold', 
                ha='right', va='bottom')

        titulo_customizado = self.entry_titulo.get().strip()
        if titulo_customizado:
            ax.set_title(titulo_customizado, fontsize=24, fontweight='bold')
        else:
            nome_arquivo = os.path.splitext(os.path.basename(caminho_csv))[0]
            ax.set_title(nome_arquivo, fontsize=24, fontweight='bold')
            
        ax.set_xlabel('Tempo (horas)', fontsize=22)
        ax.set_ylabel('Temperatura (°C)', fontsize=22)
        ax.tick_params(axis='both', which='major', labelsize=20)
        ax.grid(True, linestyle=':', alpha=0.7)
        
        # Lógica do Eixo Y
        temp_max_global = df[colunas_temperatura].max().max()
        ymin_padrao = 0
        ymax_padrao = max(temp_max_global + 10, 75)

        try:
            str_ymin = self.entry_ymin.get().replace(',', '.')
            str_ymax = self.entry_ymax.get().replace(',', '.')
            str_ystep = self.entry_ystep.get().replace(',', '.')

            ymin_val = float(str_ymin) if str_ymin.strip() else ymin_padrao
            ymax_val = float(str_ymax) if str_ymax.strip() else ymax_padrao
            ax.set_ylim(bottom=ymin_val, top=ymax_val)

            if str_ystep.strip():
                ystep_val = float(str_ystep)
                if ystep_val > 0:
                    ticks = np.arange(ymin_val, ymax_val + ystep_val, ystep_val)
                    ax.set_yticks(ticks)

        except ValueError:
            ax.set_ylim(bottom=ymin_padrao, top=ymax_padrao)

        # Lógica do Eixo X
        ax.set_xlim(left=0) 
        try:
            str_xmin = self.entry_xmin.get().replace(',', '.')
            str_xmax = self.entry_xmax.get().replace(',', '.')
            str_xstep = self.entry_xstep.get().replace(',', '.')

            if str_xmin.strip() or str_xmax.strip():
                xmin_val = float(str_xmin) if str_xmin.strip() else 0.0
                if str_xmax.strip():
                    ax.set_xlim(left=xmin_val, right=float(str_xmax))
                else:
                    ax.set_xlim(left=xmin_val)

            if str_xstep.strip():
                xstep_val = float(str_xstep)
                if xstep_val > 0:
                    c_xmin, c_xmax = ax.get_xlim()
                    ticks_x = np.arange(c_xmin, c_xmax + xstep_val, xstep_val)
                    ax.set_xticks(ticks_x)
        except ValueError:
            pass 

        if self.var_mostrar_legenda.get():
            ax.legend(
                loc='upper center', 
                bbox_to_anchor=(0.5, -0.15), 
                ncol=4, 
                fontsize=20,
                frameon=False 
            )

        if self.canvas_grafico:
            self.canvas_grafico.get_tk_widget().destroy()

        self.canvas_grafico = FigureCanvasTkAgg(fig, master=self.frame_direito)
        self.canvas_grafico.draw()
        
        widget_canvas = self.canvas_grafico.get_tk_widget()
        widget_canvas.pack(fill=tk.BOTH, expand=True)

        plt.close(fig)

if __name__ == "__main__":
    app = AplicativoGraficos()
    app.mainloop()
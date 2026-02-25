import os
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
        self.entries_legendas = [] # Guarda os campos de texto dinâmicos das legendas

        # --- CONSTRUÇÃO DA INTERFACE ---
        
        # Frame Esquerdo Principal
        self.frame_esquerdo = tk.Frame(self, width=330, bg="#f0f0f0")
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

        # CONTROLES DO EIXO Y
        self.frame_controles = tk.LabelFrame(self.scrollable_frame, text="Controles do Eixo Y (Ordenadas)", bg="#f0f0f0", font=("Arial", 9, "bold"))
        self.frame_controles.pack(fill=tk.X, pady=5, ipadx=5, ipady=5)

        tk.Label(self.frame_controles, text="Y Inicial:", bg="#f0f0f0").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.entry_ymin = tk.Entry(self.frame_controles, width=10)
        self.entry_ymin.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        tk.Label(self.frame_controles, text="Y Final:", bg="#f0f0f0").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.entry_ymax = tk.Entry(self.frame_controles, width=10)
        self.entry_ymax.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        tk.Label(self.frame_controles, text="Amplitude:", bg="#f0f0f0").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.entry_ystep = tk.Entry(self.frame_controles, width=10)
        self.entry_ystep.grid(row=2, column=1, sticky="w", padx=5, pady=5)

        tk.Label(self.frame_controles, text="Deixe em branco para o modo automático.", bg="#f0f0f0", fg="gray", font=("Arial", 8, "italic")).grid(row=3, column=0, columnspan=2, pady=(0,5))

        # --- NOVO: CONTROLES DA LEGENDA ---
        self.frame_legenda = tk.LabelFrame(self.scrollable_frame, text="Configurações da Legenda", bg="#f0f0f0", font=("Arial", 9, "bold"))
        self.frame_legenda.pack(fill=tk.X, pady=5, ipadx=5, ipady=5)

        # Checkbox para ativar/desativar
        self.var_mostrar_legenda = tk.BooleanVar(value=True)
        self.chk_mostrar_legenda = tk.Checkbutton(
            self.frame_legenda, text="Mostrar Legenda no Gráfico", 
            variable=self.var_mostrar_legenda, bg="#f0f0f0"
        )
        self.chk_mostrar_legenda.pack(anchor="w", padx=5, pady=(0, 5))

        # Frame interno onde as lacunas de nomes serão criadas dinamicamente
        self.frame_nomes_series = tk.Frame(self.frame_legenda, bg="#f0f0f0")
        self.frame_nomes_series.pack(fill=tk.X, padx=5)

        # Botão Aplicar Configurações
        self.btn_aplicar = tk.Button(
            self.scrollable_frame, 
            text="Aplicar Alterações ao Gráfico", 
            command=self.atualizar_grafico_atual,
            font=("Arial", 9, "bold"),
            bg="#e0e0e0",
            pady=5
        )
        self.btn_aplicar.pack(fill=tk.X, pady=(10, 5))

        # BOTÃO DE SALVAR IMAGEM
        self.btn_salvar = tk.Button(
            self.scrollable_frame, 
            text="💾 Salvar Gráfico (PNG)", 
            command=self.salvar_grafico,
            font=("Arial", 10, "bold"),
            bg="#28a745", fg="white", 
            relief=tk.FLAT, pady=8
        )
        self.btn_salvar.pack(fill=tk.X, pady=(5, 10))


        # --- Frame Direito (Gráfico) ---
        self.frame_direito = tk.Frame(self, bg="white", relief=tk.SUNKEN, borderwidth=1)
        self.frame_direito.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(0, 10), pady=10)
        
        self.label_aviso = tk.Label(
            self.frame_direito, 
            text="Selecione uma pasta para carregar os arquivos.\nDepois, clique em um arquivo na lista para ver o gráfico.", 
            bg="white", font=("Arial", 12)
        )
        self.label_aviso.pack(expand=True)

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
                    self.lista_arquivos.insert(tk.END, arquivo) 

        if not self.arquivos_encontrados:
            messagebox.showinfo("Aviso", "Nenhum arquivo .csv encontrado nessa pasta.")
        else:
            self.label_aviso.config(text="Arquivos carregados!\nClique em um item na lista à esquerda para visualizar.")

    def ao_selecionar_arquivo(self, event):
        selecao = self.lista_arquivos.curselection()
        if not selecao:
            return
        
        indice = selecao[0]
        self.arquivo_atual = self.arquivos_encontrados[indice]
        # Passa novo_arquivo=True para reconstruir a lista de legendas na interface
        self.gerar_e_mostrar_grafico(self.arquivo_atual, novo_arquivo=True)

    def atualizar_grafico_atual(self):
        if self.arquivo_atual:
            # Passa novo_arquivo=False para apenas ler o que o usuário digitou e atualizar
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

    def gerar_e_mostrar_grafico(self, caminho_csv, novo_arquivo=False):
        if self.label_aviso.winfo_ismapped():
            self.label_aviso.pack_forget()

        # 1. Leitura
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

        # --- LÓGICA DE ATUALIZAÇÃO DOS CAMPOS DE LEGENDA ---
        if novo_arquivo:
            # Se for um arquivo novo, limpamos os campos antigos e criamos novos
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
                ent.insert(0, nome_original) # Preenche com o nome padrão
                ent.pack(side=tk.LEFT, fill=tk.X, expand=True)
                
                self.entries_legendas.append(ent)

        # Recolhe os nomes que estão atualmente digitados nas lacunas
        nomes_para_plotar = []
        for ent in self.entries_legendas:
            nome_digitado = ent.get().strip()
            nomes_para_plotar.append(nome_digitado if nome_digitado else "Série Desconhecida")


        # 3. Construindo a Figura
        fig, ax = plt.subplots(figsize=(8, 5), constrained_layout=True)
        cores_linhas = plt.cm.tab10.colors

        # Plota as curvas de temperatura com os nomes escolhidos pelo usuário
        for i, col in enumerate(colunas_temperatura):
            nome_serie = nomes_para_plotar[i] if i < len(nomes_para_plotar) else f"Série {i+1}"
            cor = cores_linhas[i % len(cores_linhas)] 
            ax.plot(df[coluna_tempo], df[col], linewidth=2, label=nome_serie, color=cor)

        ax.axhline(y=65, color='red', linestyle='--', linewidth=1.5, label='Limite')

        titulo_customizado = self.entry_titulo.get().strip()
        if titulo_customizado:
            ax.set_title(titulo_customizado, fontsize=12, fontweight='bold')
        else:
            # os.path.splitext divide em ('B13', '.csv') e o [0] pega só o 'B13'
            nome_arquivo = os.path.splitext(os.path.basename(caminho_csv))[0]
            ax.set_title(nome_arquivo, fontsize=12, fontweight='bold')
            
        ax.set_xlabel('Tempo (horas)', fontsize=10)
        ax.set_ylabel('Temperatura (°C)', fontsize=10)
        ax.grid(True, linestyle=':', alpha=0.7)
        
        # Eixo Y Customizado
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

        ax.set_xlim(left=0)

        # Adiciona a legenda apenas se o checkbox estiver marcado
        if self.var_mostrar_legenda.get():
            ax.legend(
                loc='upper center', 
                bbox_to_anchor=(0.5, -0.15), 
                ncol=4, 
                fontsize=9,
                frameon=False 
            )

        # Atualiza a interface
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
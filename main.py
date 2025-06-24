import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import random
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
# from math import*
import tkinter.font as font
plt.rcParams['font.family'] = 'MS Gothic'

class Game:
    def __init__(self, master):
        self.master = master
        self.my_font = font.Font(size=20)
        
        self.master.title("相場予想投資ゲーム")

        # self.total_days = simpledialog.askinteger("ゲーム日数", "何日間プレイしますか？", minvalue=1, maxvalue=365)
        self.total_days = 100 # 日数
        if not self.total_days:
            self.total_days = 100

        elif self.total_days >= 365: self.total_days = 365
        elif self.total_days < 10: self.total_days = 10

        self.ohcl = [] # [(day, start, heigh, lower, end)] -> 毎日の変化を格納
        self.day = 0 # 日数
        self.price = 10_000 # 株価
        self.start_money = 1_000_000
        self.money = self.start_money # 所持金
        self.view_start = 0 # スクロール
        self.stock = 0 # 持ち株数
        self.coefficient = 3.0
        self.daily_changes = []
        self.colors = []  # 色指定リスト
        self.SCROLL = True # スクロールバーを出すかどうか

        # 乱数一回あたりの変動幅
        self.rev = 1
        self.up_width = 10 * self.rev # up の初期値
        self.lower_width = -10 * self.rev # down の初期値
        self.up, self.lower = 0, 0 # 変化させる変数
        self.ten = 10 ** 6

        self.my_font = font.Font(size=20)

        self.event_txt = [line.rstrip("\n").split(",") for line in open("event_list.csv", encoding="utf-8")]
        self.event_rand = 0.15 # イベントを起こす確率
        self.event_list = [[i[0], int(i[2]) / 10 * self.rev, int(i[3]) / 10 * self.rev] for i in self.event_txt]
        self.event_up = 0
        self.event_down = 0
        # self.canvas_frame = tk.Frame(master)
        # self.canvas_frame.pack()
        # キャンパス
        self.fig, self.ax = plt.subplots(figsize=(10, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.master)
        self.canvas.get_tk_widget().pack()

        # entry
        self.entry = tk.Entry(master)
        self.entry.insert(0, "1")
        self.entry.pack()

        self.label = tk.Label(self.master, font=("Meiryo", 14))
        self.label.pack()

        if self.SCROLL:
            # スクロールバー
            self.scroll = ttk.Scale(self.master, from_=0, to=0, orient="horizontal", command=self.on_scroll)
            self.scroll.pack(fill="x", padx=20)

        # 売買
        # 買うボタン
        self.button_buy = tk.Button(self.master, text="買う", command=self.buy)
        self.button_buy.pack(side=tk.LEFT, expand=True, fill=tk.X)

        # 売るボタン
        self.button_sell = tk.Button(self.master, text="売る", command=self.sell)
        self.button_sell.pack(side=tk.LEFT, expand=True, fill=tk.X)

        # 「次の日へ」ボタン
        self.button = tk.Button(self.master, text="次の日", command=self.skip)
        self.button.pack(side=tk.LEFT, expand=True, fill=tk.X)

        self.draw_chart()
        

    def buy(self):
        amt = self.get_amount()
        cost = self.price * amt
        if self.money >= cost:
            self.money -= cost
            self.stock += amt
            self.start_new_day()
        else:
            messagebox.showwarning("エラー", "所持金が足りません")

    def sell(self):
        amt = self.get_amount()
        if self.stock >= amt:
            self.money += self.price * amt
            self.stock -= amt
            self.start_new_day()
        else:
            messagebox.showwarning("エラー", "株が足りません")

    def skip(self):
        self.start_new_day()

    def start_new_day(self):
        if self.day >= self.total_days:
            # ▶ 最終日：すべて売却
            self.money += self.stock * self.price
            self.stock = 0
            final = self.money
            mark = ""
            if final > self.start_money: mark = "+"
            elif final == self.start_money: mark = "±"
            else: mark = "-"
            messagebox.showinfo("ゲーム終了", 
                f"{self.total_days}日経過しました！ \n初期資産: {self.start_money:,}円 \n最終資産: {final:,}円 \n収支: {mark}{abs(final - self.start_money):,} ( {mark}{abs(round((final - self.start_money) / self.start_money * 100, 2)):,}%)")
            self.master.destroy()
            exit()

        self.day += 1
        self.coefficient = 5 if random.random() < 0.05 else 1  # イベント発生率5%
        self.simulate_day() # ここで次の金額などを計算
        self.update_chart() # ここで表示などを作成（更新）

    def update_chart(self):
        self.label.config(
            text=f"{self.day}日目 | 株価: {self.price:,}円 | 所持金: {self.money:,}円 | 最大取得株数: {self.money // self.price:,} | 保有株: {self.stock:,}"
        )

        # 箱ひげ図のカスタムカラー描画
        for i, data in enumerate(self.daily_changes):
            box = self.ax.boxplot(data, positions=[i], widths=0.6, patch_artist=True, showmeans=True)
            for patch in box['boxes']:
                patch.set_facecolor(self.colors[i])

        self.ax.set_title("日別の株価変動（箱ひげ図）", fontsize=12)
        self.ax.set_xlabel("日数")
        self.ax.set_ylabel("株価")
        self.ax.set_xticks(range(len(self.daily_changes)))
        self.ax.set_xticklabels([f"{i+1}" for i in range(len(self.daily_changes))])

        # canvas = FigureCanvasTkAgg(self.fig, master=self.canvas_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack()

    # event関数
    def event(self, name, up, down):
        messagebox.showinfo("イベント発生!", f"\n{name}") # \n{up, down}")

        # up, down の幅を変更
        self.up += up
        self.lower -= down
        # print("->", up, down)


    # 収束関数
    def conve(self, lower, up):
        lower /= 1.75
        up /= 2
        return lower, up
    

    def simulate_day(self):
        # ここに確率をつける予定 -> ここにつけると売買の終了後乱数を生成しするため1000回は下がる ->> これで良いかを確認
        prices = [self.price * self.ten]
        event_bool = True if self.event_rand > random.random() else False
        if event_bool:
            event_idx = random.randint(0, len(self.event_list)-1)
            # ここでイベントを起こす
            name = self.event_list[event_idx][0]
            up = self.event_list[event_idx][1]
            down = self.event_list[event_idx][2]
            self.event(name, up, down)

        # ここでup, down を基本の値に収束する
        self.lower, self.up = self.conve(self.lower, self.up)
        inp_lower, inp_up = round((self.lower + self.lower_width) * self.ten), round((self.up + self.up_width) * self.ten)
        print(f"{inp_lower * 10 / self.ten }, {inp_up * 10 / self.ten}", f"{inp_lower} {inp_up}")

        for _ in range(1000):
            change = random.randint(inp_lower, inp_up)
            prices.append(max(prices[-1] + change, 1))
        
        for i in range(len(prices)):
            prices[i] //= self.ten

        start = prices[0]
        heigh = max(prices)
        lower = min(prices)
        end = prices[-1]
        
        self.ohcl.append([self.day, start, heigh, lower, end])
        self.price = end

        if self.day > 30:
            self.view_start = self.day - 30

        else:
            self.view_start = 0

        if self.SCROLL:
            max_scroll = max(0, self.day - 30)
            self.scroll.config(to = max_scroll)
            self.scroll.set(self.view_start)

        self.draw_chart()


    def on_scroll(self, val):
        self.view_start = int(float(val))
        self.draw_chart()

    def get_amount(self):
        try:
            return max(0, int(self.entry.get()))
        except ValueError:
            return 0

    def draw_chart(self):
        self.ax.clear()
        self.ax.set_title("株価シミュレーション")
        self.ax.set_xlabel("日")
        self.ax.set_ylabel("株価")

        view_data = self.ohcl[self.view_start:self.view_start + 30]

        for i, (day, start, heigh, lower, end) in enumerate(view_data):
            color = "red" if end >= start else "green"
            x = day
            widgh = 0.6

            self.ax.plot([x, x], [lower, heigh], color="black") # ひげ
            self.ax.bar(x, end - start, width=widgh, bottom=start, color=color, edgecolor="black") # 本体
    
        self.ax.set_xlim(max(-0.5, self.day-20), self.day+10)
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw()


if __name__ == "__main__":
    root = tk.Tk()
    game = Game(root)
    root.mainloop()

# 思っていることリスト
# スクロールバーいる？　-> 使う機械がない => ok
# ↑戻す必要すらない気がする => ok
# 買った値段がわかればいいかも -> 実装はちょっとめんどそうだけど技術的には可能 => ok
# ↑売った時にどれを売るかがわからないため．そこが問題になってくる気がする => ok
# 前から売っていくなら平均とかも出せる -> 問題は↑と同じ => ok
# そのほかになんかいいアイデアがあれば実装する -> 多分出てこない気がする and 出てきたとしたらめんどくさい


# 実装しないといけないことリスト
# csvかなんかのファイルに格納されたイベントを引き出す部分
# イベントの発生を知らせる関数 -> イベントを起こすように変更する
# upもdownの幅を決めてそこから乱数で決めることで固定化を解消
# 徐々にもどうしていくように変更 -> ここも幅を決めて乱数にするのもあり
# 振れ幅を乱数で決めて収束幅も乱数で決める -> その乱数の幅をイベントのファイルに書き込み読み込んぬ時にlistで管理して上手いことやる
# イベントはメッセージボックスとかのほうが良い気がする．確率をかなり小さくし，1000回の乱数の途中で入れることによりバランスを調整 -> 乱数生成前でも良い気もする
# 間に入れることにより，いいときに売買するのを防ぐ -> イメージとして30 ~ 60日に一回くらい起きてもいいかも

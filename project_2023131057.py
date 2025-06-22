import random
from collections import Counter

RANKS = [str(i) for i in range(1, 11)]  # 1~10 숫자 카드

# 숫자 카드 덱 생성 (중복 허용)
def create_deck():
    return RANKS * 4  # 총 40장 (1~10 각각 4장씩)

# 핸드 강도 평가 함수 및 조합 정보 반환
def evaluate_hand(hand, community):
    cards = list(map(int, hand + community))  # 숫자형 카드 목록
    count = Counter(cards)  # 각 숫자의 빈도 계산
    counts = sorted(count.values(), reverse=True)
    unique = sorted(set(cards))

    is_straight = False  # 스트레이트 여부
    high_card = 0
    # 스트레이트 확인
    if len(unique) >= 5:
        for i in range(len(unique) - 4):
            if unique[i+4] - unique[i] == 4 and unique[i+1] - unique[i] == 1:
                is_straight = True
                high_card = unique[i+4]
                break

    # 조합에 따라 핸드 강도 평가
    if 4 in counts:
        rank = max(k for k, v in count.items() if v == 4)
        return (7 + rank / 100, '포카드', rank)
    elif 3 in counts and 2 in counts:
        rank = max(k for k, v in count.items() if v == 3)
        return (6 + rank / 100, '풀하우스', rank)
    elif is_straight:
        return (5 + high_card / 100, '스트레이트', high_card)
    elif 3 in counts:
        rank = max(k for k, v in count.items() if v == 3)
        return (4 + rank / 100, '트리플', rank)
    elif counts.count(2) >= 2:
        rank = max(k for k, v in count.items() if v == 2)
        return (3 + rank / 100, '투페어', rank)
    elif 2 in counts:
        rank = max(k for k, v in count.items() if v == 2)
        return (2 + rank / 100, '원페어', rank)
    else:
        rank = max(cards)
        return (1 + rank / 100, '하이카드', rank)

# 플레이어 클래스
class Player:
    def __init__(self, name):
        self.name = name
        self.hand = []  # 비공개 카드
        self.chips = 60  # 시작 칩 수
        self.folded = False
        self.eliminated = False
        self.hand_score = (0, '', 0)  # (점수, 조합 이름, 주 랭크)

    def __repr__(self):
        return f"{self.name}: 칩: {self.chips}"

# 저격 홀덤 게임 클래스
class SniperHoldem:
    def __init__(self, player_names):
        self.players = [Player(name) for name in player_names]
        self.deck = []
        self.community_cards = []  # 공개 카드 4장
        self.pot = 0  # 판돈
        self.banned_combo = None  # 저격된 조합

    # 카드 배분
    def deal(self):
        self.deck = create_deck()
        random.shuffle(self.deck)
        self.community_cards = [self.deck.pop() for _ in range(4)]
        for player in self.players:
            player.hand = [self.deck.pop(), self.deck.pop()]
            player.hand_score = evaluate_hand(player.hand, self.community_cards)

    # 베팅 라운드
    def betting_round(self, is_first_round=False):
        print("\n-- 베팅 라운드 시작 --")
        for player in self.players:
            if not player.folded and not player.eliminated:
                while True:
                    try:
                        print(f"{player.name}의 차례입니다. 현재 칩: {player.chips}")
                        bet = int(input(f"베팅할 칩 수를 입력하세요 (최소 1, 최대 {player.chips}): "))
                        if 1 <= bet <= player.chips:
                            player.chips -= bet
                            self.pot += bet
                            if bet == 1 and is_first_round:
                                player.folded = True
                                print(f"{player.name}는 해당 라운드를 포기하며 1칩을 소모합니다.")
                            else:
                                print(f"{player.name}가 {bet}칩 베팅함. 남은 칩: {player.chips}")
                            break
                        else:
                            print("1 이상 보유 칩 이하로 입력하세요.")
                    except ValueError:
                        print("숫자를 입력하세요.")

    # 저격 라운드
    def sniper_round(self):
        print('-- 저격 라운드 시작 --')
        guesses = []
        for sniper in self.players:
            if sniper.eliminated or sniper.folded:
                continue
            print(f"{sniper.name}의 저격 차례입니다.")
            while True:
                try:
                    guess_input = input("저격할 패를 입력하세요 (예: '4 트리플'): ").strip()
                    parts = guess_input.split()
                    if len(parts) != 2:
                        print("형식은 '숫자 조합명'이어야 합니다. 예: '4 트리플'")
                        continue
                    guess_rank, guess_combo = parts
                    if guess_combo not in ['포카드', '풀하우스', '스트레이트', '트리플', '투페어', '원페어', '하이카드']:
                        print("올바른 조합명을 입력하세요.")
                        continue
                    guess_rank = int(guess_rank)
                    if 1 <= guess_rank <= 10:
                        guesses.append((sniper.name, guess_combo, guess_rank))
                        break
                    else:
                        print("1에서 10 사이의 숫자를 입력하세요.")
                except ValueError:
                    print("숫자를 입력하세요.")

        # 저격 성공 확인
        banned = []
        for sniper_name, guess_combo, guess_rank in guesses:
            for player in self.players:
                if player.eliminated:
                    continue
                _, combo, rank = player.hand_score
                if combo == guess_combo and rank == guess_rank:
                    print(f"{sniper_name}의 저격 성공: {player.name}의 '{guess_rank} {guess_combo}' 저격됨")
                    banned.append((guess_combo, guess_rank))
        if banned:
            self.banned_combo = banned[-1]  # 마지막 성공한 저격만 적용
        else:
            print("모든 저격 실패! 일반 핸드 비교로 넘어갑니다.")

    # 라운드 결과 처리
    def resolve_round(self):
        print("\n-- 라운드 결과 정리 --")
        active_players = [p for p in self.players if not p.folded and not p.eliminated]
        if not active_players:
            print("모두 폴드하여 승자 없음.")
            return

        # 저격된 조합 제외
        if self.banned_combo:
            combo_name, combo_rank = self.banned_combo
            active_players = [p for p in active_players if not (p.hand_score[1] == combo_name and p.hand_score[2] == combo_rank)]
            print(f"저격된 패 '{combo_rank} {combo_name}'는 제외됩니다.")
            self.banned_combo = None

        if not active_players:
            print("모든 유효한 핸드가 저격되어 승자 없음.")
            return

        winner = max(active_players, key=lambda p: p.hand_score[0])
        print(f"{winner.name}가 팟 {self.pot}칩을 획득합니다!")
        winner.chips += self.pot
        self.pot = 0
        for p in self.players:
            p.folded = False

    # 탈락자 확인
    def check_elimination(self):
        for p in self.players:
            if p.chips <= 0:
                p.eliminated = True
                print(f"{p.name} 탈락!")
            elif p.chips >= 75:
                surplus = p.chips - 75
                p.chips = 75
                p.eliminated = True
                print(f"{p.name}는 75칩을 달성하여 게임에서 탈출합니다! 잔여 칩 {surplus}개를 분배합니다.")
                recipients = [pl for pl in self.players if not pl.eliminated and pl != p]
                if recipients:
                    share = surplus // len(recipients)
                    for r in recipients:
                        r.chips += share
                    print(f"각 남은 플레이어는 {share}칩씩 받았습니다.")

    # 현재 게임 상태 출력
    def show_state(self):
        print("\n=== 현재 상태 ===")
        for player in self.players:
            status = "(제외)" if player.eliminated else ""
            print(f"{player} {status}")
        print(f"공유 카드: {self.community_cards}")
        print(f"현재 팟: {self.pot}\n")

    # 게임 실행
    def play_game(self):
        round_count = 1
        while True:
            print(f"\n========== 라운드 {round_count} ==========")
            self.deal()
            self.show_state()
            for player in self.players:
                if not player.eliminated:
                    input(f"[{player.name}]의 비공개 카드를 보려면 Enter를 누르세요...")
                    print(f"{player.name}의 비공개 카드: {player.hand}")
            self.betting_round(is_first_round=True)
            self.sniper_round()
            self.show_state()
            self.resolve_round()
            self.check_elimination()
            alive_players = [p for p in self.players if not p.eliminated]
            if len(alive_players) == 1:
                print(f"\n{alive_players[0].name} 최종 승리!")
                break
            round_count += 1

# 게임 시작
if __name__ == "__main__":
    game = SniperHoldem(["플레이어1", "플레이어2", "플레이어3", "플레이어4"])
    game.play_game()

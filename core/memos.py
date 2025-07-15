# 目前 MemoManager 主要逻辑已在 MemoDialog 中实现，如需后端存储/管理可在此扩展
class MemoManager:
    def __init__(self):
        self.memos = []
    def add_memo(self, memo):
        self.memos.append(memo)
    def get_memos(self):
        return self.memos
    def update_memo(self, index, memo):
        if 0 <= index < len(self.memos):
            self.memos[index] = memo
    def delete_memo(self, index):
        if 0 <= index < len(self.memos):
            del self.memos[index] 
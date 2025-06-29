import os
import streamlit as st
import json
import pandas as pd
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import GPT4AllEmbeddings
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from src.models import using_llm_groq
from src.prompts import CUSTORM_AGENT_SYSTEM_TEMPLATE
from src.global_settings import VECTOR_DB_PATH, EMBEDDING_MODEL_FILE, CHAT_HISTORY_FILE
from datetime import datetime
from src.common.utils import logger, display_message

class ConversationEngine:
    def __init__(self, username: str = "default_user", user_info: dict = {}):
        self.username = username
        self.user_info = user_info
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY không được tìm thấy. Kiểm tra tệp .env.")
        self.llm = using_llm_groq(api_key=api_key)
        self.db = self.load_vector_db()
        self.qa_chain = self.create_qa_chain()
        # Đọc từ khóa từ file CSV
        self.direct_query_keywords = self.load_keywords("data/keywords/direct_query_keywords.csv")
        self.emotion_keywords = self.load_keywords("data/keywords/emotion_keywords.csv")
        self.personal_keywords = self.load_keywords("data/keywords/personal_keywords.csv")
        # Danh sách cảm xúc tích cực
        self.positive_emotions = ["vui", "hạnh phúc", "phấn khởi", "hào hứng", "yêu đời", "thư giãn"]

    def load_keywords(self, file_path):
        """Đọc từ khóa từ file CSV"""
        try:
            df = pd.read_csv(file_path)
            keywords = df["keyword"].dropna().tolist()
            return keywords
        except Exception as e:
            logger.error(f"Lỗi khi đọc file {file_path}: {str(e)}")
            return []

    def load_vector_db(self):
        try:
            embedding_model = GPT4AllEmbeddings(model_file=EMBEDDING_MODEL_FILE)
            return FAISS.load_local(VECTOR_DB_PATH, embedding_model, allow_dangerous_deserialization=True)
        except Exception as e:
            raise RuntimeError(f"Lỗi khi tải Vector DB: {str(e)}")

    def create_qa_chain(self):
        prompt = PromptTemplate(
            template=r"""
Bạn là một trợ lý AI chuyên về sức khỏe tâm thần, được thiết kế để hỗ trợ người dùng bằng tiếng Việt. Dựa hoàn toàn trên thông tin từ DSM-5 trong cơ sở dữ liệu, hãy cung cấp câu trả lời chi tiết, đầy đủ và chính xác cho câu hỏi của người dùng. 

- Nếu câu hỏi không liên quan đến cảm xúc cá nhân (như không chứa từ khóa từ emotion_keywords hoặc personal_keywords), hãy trả lời trực tiếp dựa trên định nghĩa, tiêu chuẩn chẩn đoán, triệu chứng, và điều trị từ DSM-5 mà không đưa ra câu hỏi trắc nghiệm.
- Nếu câu hỏi liên quan đến cảm xúc cá nhân:
  - Với cảm xúc tiêu cực (như buồn, lo âu, căng thẳng), phân tích mức độ (nhẹ, trung bình, nặng) và đưa ra gợi ý dựa trên tiêu chuẩn chẩn đoán DSM-5.
  - Với cảm xúc tích cực (như vui, hạnh phúc, phấn khởi), giải thích ý nghĩa của cảm xúc đó trong bối cảnh sức khỏe tâm thần, cung cấp thông tin tích cực từ DSM-5 (nếu có) hoặc từ kiến thức tâm lý học chung, và đưa ra gợi ý để duy trì trạng thái tích cực. Không mặc định trả lời về rối loạn khi cảm xúc là tích cực.

Trả lời rõ ràng, chi tiết và hoàn toàn bằng tiếng Việt.

{context}

Câu hỏi: {question}
""",
            input_variables=["context", "question"]
        )
        return RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.db.as_retriever(search_kwargs={"k": 3}, max_token_limit=512),
            return_source_documents=True,
            chain_type_kwargs={'prompt': prompt}
        )

    def chat(self, user_input):
        prompt = CUSTORM_AGENT_SYSTEM_TEMPLATE.format(user_info=self.user_info) + f"\n\nNgười dùng: {user_input}"
        response = self.qa_chain.invoke({"query": prompt})
        return response.get("result", "Không tìm thấy thông tin phù hợp trong DSM-5.")

    def process_direct_query(self, prompt):
        response = self.chat(prompt)
        return {
            "question": None,
            "options": [],
            "response": response
        }

    def generate_question(self, prompt):
        prompt_lower = prompt.lower()
        emotion = next((keyword for keyword in self.emotion_keywords if keyword in prompt_lower), None)
        
        if emotion:
            question = f"Trong tuần qua, bạn có cảm thấy {emotion} đến mức ảnh hưởng đến giấc ngủ, công việc hoặc các hoạt động hàng ngày không?"
            options = ["Không bao giờ", "Hiếm khi", "Đôi khi", "Thường xuyên", "Luôn luôn"]
            response = f"Mình hiểu bạn đang cảm thấy {emotion}. Hãy chọn mức độ phù hợp nhất với bạn:"
            return {
                "question": question,
                "options": options,
                "response": response
            }
        else:
            return {
                "question": None,
                "options": [],
                "response": "Mình không nhận diện được cảm xúc trong câu của bạn. Hãy chia sẻ thêm nhé!"
            }

    def process_answer(self, prompt, question, answer):
        prompt_lower = prompt.lower()
        emotion = next((keyword for keyword in self.emotion_keywords if keyword in prompt_lower), "buồn")
        severity_mapping = {"Không bao giờ": "nhẹ", "Hiếm khi": "nhẹ", "Đôi khi": "trung bình", "Thường xuyên": "nặng", "Luôn luôn": "rất nặng"}
        severity = severity_mapping.get(answer, "trung bình")

        # Kiểm tra xem cảm xúc có phải là tích cực không
        is_positive_emotion = emotion in self.positive_emotions

        if is_positive_emotion:
            # Với cảm xúc tích cực, trả lời tích cực và gợi ý duy trì trạng thái
            query = f"Ý nghĩa của cảm xúc {emotion} trong sức khỏe tâm thần và gợi ý duy trì trạng thái tích cực"
            response = self.qa_chain.invoke({"query": query})
            result = response.get("result", "Không tìm thấy thông tin phù hợp trong DSM-5.")
            return f"Dựa trên mức độ {severity}, cảm xúc {emotion} của bạn cho thấy một trạng thái tích cực. {result}"
        else:
            # Với cảm xúc tiêu cực, phân tích theo DSM-5
            query = f"Tiêu chuẩn chẩn đoán rối loạn {emotion} theo DSM-5 với mức độ {severity}"
            response = self.qa_chain.invoke({"query": query})
            result = response.get("result", "Không tìm thấy thông tin phù hợp trong DSM-5.")
            return f"Dựa trên mức độ {severity}, {result}"

def chat_interface(username: str, user_info: dict, container):
    chat_store = []
    if os.path.exists(CHAT_HISTORY_FILE) and os.path.getsize(CHAT_HISTORY_FILE) > 0:
        try:
            with open(CHAT_HISTORY_FILE, "r") as f:
                chat_store = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Lỗi khi đọc CHAT_HISTORY_FILE: {e}")
            chat_store = []

    if not chat_store:
        with container:
            with st.chat_message(name="assistant"):
                st.markdown("Chào bạn, mình là Chatbot. Mình sẽ giúp bạn chăm sóc sức khỏe tinh thần. Hãy cho mình biết tình trạng của bạn hoặc bạn có thể trò chuyện với mình nhé!")

    if "waiting_for_answer" not in st.session_state:
        st.session_state.waiting_for_answer = False
    if "current_question" not in st.session_state:
        st.session_state.current_question = None
    if "current_options" not in st.session_state:
        st.session_state.current_options = []
    if "answered" not in st.session_state:
        st.session_state.answered = False

    agent = ConversationEngine(username, user_info)
    display_message(chat_store, container, username)

    user_input = st.chat_input("Nhập tin nhắn của bạn tại đây...",)
    if user_input:
        with container:
            with st.chat_message(name="user"):
                st.markdown(user_input)
            response_data = agent.generate_question(user_input) if any(keyword in user_input.lower() for keyword in agent.personal_keywords) and any(emotion in user_input.lower() for emotion in agent.emotion_keywords) else agent.process_direct_query(user_input)
            
            with st.chat_message(name="assistant"):
                st.markdown(response_data.get("response", "Không tìm thấy thông tin phù hợp."))
                if response_data.get("question"):
                    st.session_state.waiting_for_answer = True
                    st.session_state.current_question = response_data["question"]
                    st.session_state.current_options = response_data["options"]
                    st.session_state.answered = False

        if st.session_state.waiting_for_answer and not st.session_state.answered:
            with container:
                with st.chat_message(name="assistant"):
                    st.write(f"**Câu hỏi**: {st.session_state.current_question}")
                    options = st.session_state.current_options
                    answer = st.radio("Chọn mức độ:", options, key=f"radio_{user_input}")
                    if answer:
                        st.session_state.answered = True
                        st.session_state.waiting_for_answer = False
                        with st.chat_message(name="user"):
                            st.markdown(answer)
                        new_response = agent.process_answer(user_input, st.session_state.current_question, answer)
                        with st.chat_message(name="assistant"):
                            st.markdown(new_response)
                        st.session_state.current_question = None
                        st.session_state.current_options = []

        chat_store.append({"role": "user", "content": user_input, "time": datetime.now().strftime("%H:%M:%S %d-%m-%Y")})
        chat_store.append({"role": "assistant", "content": response_data.get("response", ""), "time": datetime.now().strftime("%H:%M:%S %d-%m-%Y")})
        try:
            with open(CHAT_HISTORY_FILE, "w") as f:
                json.dump(chat_store, f, indent=4)
        except Exception as e:
            logger.error(f"Lỗi khi lưu CHAT_HISTORY_FILE: {e}")
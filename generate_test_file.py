import os

target_size = 10 * 1024 * 1024
file_path = 'test_10mb_constitution.txt'
sample_text = """Article 14 of the Constitution of India provides for equality before the law or equal protection of the laws within the territory of India.
Article 15 secures the citizens from every sort of discrimination by the State, on the grounds of religion, race, caste, sex or place of birth or any of them.
Article 19 guarantees the citizens of India the following six fundamental freedoms: Freedom of speech and expression, Freedom of assembly, Freedom to form associations, Freedom of movement, Freedom to reside and settle, Freedom of profession, occupation, trade or business.
Article 21 states that no person shall be deprived of his life or personal liberty except according to a procedure established by law.

"""

with open(file_path, 'w', encoding='utf-8') as f:
    current_size = 0
    while current_size < target_size:
        f.write(sample_text)
        current_size += len(sample_text.encode('utf-8'))

print(f"Generated {file_path} with size {os.path.getsize(file_path) / (1024*1024):.2f} MB")

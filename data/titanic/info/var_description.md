### statistics
- Number of variables	12
- Number of observations	891
- Missing cells	866
- Missing cells (%)	8.1%
- Duplicate rows	0
- Duplicate rows (%)	0.0%
- Total size in memory	83.7 KiB
- Average record size in memory	96.1 B

### description
| 컬럼명           | 설명                                                      | 데이터 타입        | 예시                        | 특이사항 (Alert)                     |
| ------------- | ------------------------------------------------------- | ------------- | ------------------------- | -------------------------------- |
| `PassengerId` | 승객 고유 ID                                                | 정수형 (`int`)   | 1, 892                    | ✅ **고유값**, ✅ **균등 분포 (Uniform)** |
| `Survived`    | 생존 여부<br>0 = 사망, 1 = 생존                                 | 이진 (`int`)    | 0, 1                      | ✅ **Sex 변수와 높은 상관관계**            |
| `Pclass`      | 객실 등급<br>1 = 상류층, 2 = 중류층, 3 = 하류층                      | 범주형 (`int`)   | 1, 2, 3                   | —                                |
| `Name`        | 승객 이름 (호칭 포함)                                           | 문자열 (`str`)   | `Braund, Mr. Owen Harris` | ✅ **고유값**                        |
| `Sex`         | 성별                                                      | 범주형 (`str`)   | `male`, `female`          | ✅ **Survived와 높은 상관관계**          |
| `Age`         | 나이                                                      | 실수형 (`float`) | 22.0, NaN                 | ⚠️ **결측치 177개 (19.9%)**          |
| `SibSp`       | 형제/배우자 수                                                | 정수형 (`int`)   | 1, 0                      | ⚠️ **0값 다수 (68.2%)**             |
| `Parch`       | 부모/자녀 수                                                 | 정수형 (`int`)   | 0, 2                      | ⚠️ **0값 다수 (76.1%)**             |
| `Ticket`      | 티켓 번호                                                   | 문자열 (`str`)   | `A/5 21171`               | —                                |
| `Fare`        | 승선 요금 (£)                                               | 실수형 (`float`) | 7.25                      | ⚠️ **0값 15개 (1.7%)**             |
| `Cabin`       | 객실 번호                                                   | 문자열 (`str`)   | `C85`, NaN                | ⚠️ **결측치 687개 (77.1%)**          |
| `Embarked`    | 승선 항구<br>C = Cherbourg, Q = Queenstown, S = Southampton | 범주형 (`str`)   | `S`                       |     ⚠️ **결측치 2개**                           |

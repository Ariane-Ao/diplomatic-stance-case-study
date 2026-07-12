# diplomatic-stance-case-study
A case-study skill for tracking diplomatic stance shifts, built on official White House/USTR public documents. 
面向的问题：国际关系研究里经常需要判断“某国在某议题上的立场是不是变了、什么时候变的”。直接让AI读一堆讲话稿、白皮书去总结，最容易出两个问题：一是脱离语境断章取义，把一句场面话读成强硬转向；二是为了让叙事好看，AI会倾向于夸大甚至编造某个时间点的“立场突变”。
这个Skill的设计目标不是让AI自动产出一条好看的时间线，而是在AI每一次想要标记立场转变的地方，强制停下来要求原文证据，并交给人工确认——这是它和普通AI摘要报告的本质区别，对应课程里“控制力”这条主线：工具服务于人的判断，而不是替代判断。

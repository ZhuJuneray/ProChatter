# -*- coding: utf-8 -*-

import openai
import ipdb
import traceback
import time
import re
import os
colors = ['#f7fcf5', '#c7e9c0', '#73c476', '#228a44', '#00441b']
# openai.api_key = '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'
openai.api_key = 'sk-2esy6xiQbt3jZFMglD5EkBLYBxBXrgrbhVm7jnXfv0x8WfHG'
openai.api_base = 'https://api.chatanywhere.cn/v1'
inputsss = []
answersss = []
A = [
    "请告诉我有关历史的信息。",
    "关于科学，你能告诉我些什么？",
    "跟我谈谈科技吧。",
    "讲个故事给我听。",
    "请给我一些获得成功的建议。",
    "你能告诉我关于未来的事情吗？",
    "我怎样能更幸福？",
    "有哪些好书推荐阅读？",
    "我该如何度过我的一生？",
    "我该如何提高生产力？",
    "生命的意义是什么？",
    "保持健康的最佳方法是什么？"
]
B = [
    "当然，我很乐意为您提供有关历史的概述！\n\n历史是研究过去事件、人类行动和社会发展的学科。它涵盖了广泛的主题，包括政治、文化、社会、经济和技术发展。历史的研究使我们能够了解社会是如何演变的，文化是如何互动的，个人和群体是如何塑造了我们今天生活的世界。\n\n以下是人类历史中一些关键时期和事件的简要概述：\n\n史前时期：这包括书写发明之前的时期。它包括旧石器时代、中石器时代和新石器时代，人类在这些时期内发展了工具、农业和定居社区。\n\n古代文明：这个时期包括了古代文明的兴起，如美索不达米亚人、埃及人、希腊人、罗马人等。这些文明在农业、建筑、哲学和治理方面取得了重大进展。\n\n中世纪时期：这个时代见证了封建制度的发展，基督教的传播，以及拜占庭帝国和中东伊斯兰哈里发国家的崛起。中世纪时期还包括欧洲文艺复兴，这是一个在艺术、科学和学术领域引发了新的兴趣的文化和知识运动。\n\n大航海时代：15至17世纪，欧洲探险家航行到新大陆，发现了美洲、通往亚洲的贸易路线，并扩展了殖民帝国。\n\n启蒙时代：18世纪以启蒙运动为特点，这是一场强调理性、个人主义和教会与国家分离的知识运动。像伏尔泰、卢梭和洛克这样的思想家在政治、哲学和科学方面产生了深远影响。\n\n工业革命：从18世纪末开始，工业革命带来了重大的技术进步，将经济从农业转变为工业，并导致城市化。\n\n19和20世纪：这个时期见证了重大事件，如美国内战、一战和二战、俄国革命、冷战，以及世界各地的脱殖民运动。\n\n现代时代：20世纪下半叶以来，世界迅速全球化，技术取得了进步，数字革命蓬勃发展，地缘政治变化不断进行。\n\n这只是一个非常简要的概述，还有无数事件和发展塑造了人类的历史。历史的研究帮助我们了解我们的根源，从错误中吸取教训，并欣赏那些在我们之前的人们取得的成就和奋斗。",
    "科学是一种通过观察、实验和分析来系统有序地获取关于自然界的知识的方法。其目标是理解统治宇宙中各种现象的基本原则、法则和机制。科学涵盖了广泛的学科，每个学科都专注于自然界的特定方面。以下是关于科学的一些关键要点：\n\n1.科学方法：科学方法是科学家用来进行研究的标准化方法。它涉及多个步骤，包括观察现象、制定假设、设计和进行实验、收集数据、分析结果和得出结论。这个过程是迭代的，新的观察往往会导致假设的修正和进一步的实验。\n\n2.科学分支：科学被划分为各种不同的分支或学科，每个学科都专注于特定的研究领域。一些主要的分支包括物理学、化学、生物学、天文学、地质学、心理学和社会学等。每个分支都有自己的研究方法、理论和工具，用于研究和理解自然界。\n\n3.理论与法则：在科学中，理论是一个有大量证据支持的自然现象的良好证实解释。理论的范围更广，可以用来解释广泛相关的现象。而法则描述了自然界中可观察的模式或关系，并常常以数学方程的形式表达。\n\n4.经验主义方法：科学依赖经验证据，这些证据是通过观察和实验获得的。经验证据对于验证或反驳假设和理论至关重要，确保科学知识基于具体的观察，而不是臆测。\n\n5.同行评审：科学研究需要经过同行评审，即领域内的专家在研究发表在科学期刊之前评估其质量、有效性和重要性。同行评审有助于保持科学发现的诚信和可信度。\n\n6.可证伪性：科学假设和理论必须是可测试和潜在可证伪的。这意味着它们可以通过实验或观察被证明为假。可证伪性是科学严谨性的关键方面，它防止了理论变成无法证伪的纯粹推测。\n\n7.进步性质：科学是一个动态和不断发展的过程。新的发现、技术进步和范式转变可以导致之前被接受的理论的修订甚至颠覆。这种持续改进的过程有助于科学知识随着时间的推移不断增长。\n\n8.跨学科性质：许多科学问题和挑战需要跨学科的方法，多个科学学科合作解决复杂问题。例如，生物信息学和环境科学常常涉及生物学、计算机科学等学科的整合。\n\n9.道德考虑：科学研究在确保参与者、动物和环境福祉的道德界限内进行。在医学、遗传学和心理学等领域，道德考虑尤为重要。\n\n10.应用：科学知识导致了许多技术进步和创新，改变了社会。从医疗治疗和通信技术到太空探索和可持续能源来源，科学在塑造我们现代世界中发挥着重要作用。\n\n总之，科学是理解自然界和通过知识和创新改善人类生活质量的强大工具。",
    "当然，我很乐意跟你谈谈科技！\n\n科技是一个广泛且不断发展的领域，涵盖了将科学知识应用于创造工具、系统和解决方案，以改善我们的生活和周围的世界。它深刻地改变了我们的沟通方式、工作方式、学习方式，甚至思考方式。以下是科技领域的一些关键领域和趋势：\n\n1.人工智能（AI）与机器学习：人工智能涉及开发能够执行通常需要人类智能的任务的系统，如理解自然语言、识别模式和做出决策。机器学习是AI的一个子集，侧重于根据数据训练算法，以改善它们的性能。\n\n2.物联网（IoT）：物联网是指互连的物理设备、车辆、建筑物和其他带有传感器、软件和网络连接性的物品的网络。这些设备可以收集和交换数据，导致了智能家居、工业自动化和智能城市等应用。\n\n3.区块链：区块链是一种分散和分布式的数字分类技术，可确保安全透明的交易。它以比特币等加密货币的基础技术而著名，但其潜力延伸到供应链管理、金融和医疗保健等各个行业。\n\n4.虚拟现实和增强现实（VR/AR）：虚拟现实将用户沉浸在数字环境中，而增强现实将数字内容叠加在现实世界上。这些技术的应用范围从游戏和娱乐到培训、教育，甚至远程协作。\n\n5.5G技术：第五代无线技术，5G，提供了显著更快的数据速度、更低的延迟以及同时连接大量设备的能力。它有望推动自动驾驶汽车、远程手术和物联网等领域的进步。\n\n6.生物技术：生物学和技术的交叉孕育了基因编辑（例如CRISPR）、个性化医学和生物信息学等创新。这些进步有可能彻底改变医疗保健和对生命本质的理解。\n\n7.可再生能源和可持续技术：技术在解决环境挑战方面发挥着至关重要的作用。可再生能源、节能技术和智能电网对于转向更可持续的未来至关重要。\n\n8.网络安全：随着技术的进步，保护数字系统和数据的挑战也在不断增加。网络安全涵盖了旨在保护网络、设备和信息免受未经授权的访问、攻击和数据泄漏的策略和技术。\n\n9.自主系统：从自动驾驶汽车到无人机和机器人，自主系统依赖于人工智能和传感器，在无需人类干预的情况下运行。这些系统有可能彻底改变交通、物流和制造等行业。\n\n10.量子计算：量子计算机利用量子力学原理，在远远超出传统计算机的速度下执行复杂的计算。虽然仍处于早期阶段，量子计算有望解决目前在计算上不可行的问题。\n\n这只是科技广阔领域中的一小部分。重要的是要认识到科技的影响几乎涵盖了现代生活的方方面面，塑造了我们互动、创造和探索新可能性的方式。随着科技的不断进步，伦理考虑和负责任的发展变得越来越重要，以确保最大限度地发挥其益处，同时将潜在风险降到最低。",
    "在坐落于起伏的山丘和茂密的森林之间的宁静村庄埃尔登布鲁克，住着一个名叫艾拉拉的年轻女孩。她拥有无限的好奇心和难以满足的冒险渴望，常常引领她探索周围的树林。艾拉拉最喜欢的地方是“低语树林”，一个神秘的树林，风似乎承载着秘密，树木低声诉说着古老的传说。\n\n在一个清晨，金色的叶子铺满了森林的地面，艾拉拉开始了新的旅程。带着一本破旧的皮革日记本和她的可靠地图，她踏入了比以往任何时候都更深的树林。在树叶沙沙作响和微风轻轻吹拂的引导下，她发现自己来到了一个前所未见的空地。\n\n在空地的中央矗立着一棵巨大的树，它的树干扭曲而粗糙，根似乎延伸到了地球的中心。树叶闪烁着银色的色调，树枝上饰有复杂的纹样，散发出柔和的光芒。艾拉拉感到与这棵树有一种莫名的联系，仿佛它在呼唤着她。\n\n当她靠近时，一个声音似乎在她脑海中回响。“欢迎，寻找故事的人，”它低语着。被惊吓却又感到兴趣，艾拉拉回答道：“你是谁？”\n\n“我是记忆守护者，”声音回答道，声音温和而睿智。“在我内心蕴含着时代的知识，过去的故事和未来的梦想。我一直在等待一个心灵敞开世界奥秘的人。”\n\n兴奋和忐忑交加之际，艾拉拉伸出手，触摸了树皮。刹那间，她的脑海中涌现出来自时间各个角落的图像、情感和声音。她看到王国的兴衰，孩子们的笑声，英雄的勇气以及被遗忘的爱情故事的低语。每一个记忆都是构成存在之织锦的一部分。\n\n在接下来的几天和几周里，艾拉拉回到了低语树林，从记忆守护者那里学习。她发现，通过触摸树，她可以分享自己的故事和经历，将它们添加到树的集体意识中。作为回报，她获得了智慧和洞察，丰富了她对周围世界的理解。\n\n艾拉拉与记忆守护者的联系传遍了村庄，不久，人们从远方涌来寻求她的指引。他们带来问题、困境和梦想，而艾拉拉则在树的指引下帮助他们在内心找到答案。\n\n随着季节的变化和岁月的流逝，艾拉拉被称为“村庄贤者”，她谦卑地接受这个称号。她继续分享她从记忆守护者那里学到的故事，激励着后代。虽然埃尔登布鲁克的人们最终离开，但低语树林仍然是那些寻求其秘密的人们的奇妙和慰藉之地。\n\n于是，艾拉拉和记忆守护者的故事成为了一个传奇，在树木间低语，代代相传。它讲述了故事将我们连接在一起的力量，寻找世界宁静之地中的智慧，以及那些敢于寻求它的人心中蕴藏的魔力。",
    "当然，成功对不同的人意味着不同的事情，但以下是一些建议，可以帮助你实现你的目标和愿望：\n\n1.设定明确的目标：明确定义成功对你意味着什么，设定具体、可衡量、可实现、相关和有时间限制（SMART）的目标。明确的目标给予你方向和目的。\n\n2.发展成长心态：接受挑战，从失败中学习，并相信通过努力和学习可以发展你的能力和智慧。这种心态培养了韧性和改进的意愿。\n\n3.努力工作：成功很少是不经过辛勤工作和奉献就能实现的。付出所需的时间和努力，必要时做好额外的努力。\n\n4.持续学习：始终愿意学习新的技能，获取知识，并适应不断变化的环境。持续学习使你保持相关性，并帮助你创新。\n\n5.时间管理：通过优先处理任务、设定截止日期和消除干扰，高效地管理时间。有效的时间管理可以让你在更短的时间内完成更多的事情。\n\n6.建立人脉：与你所在领域或行业的其他人建立并培养有意义的关系。人际网络可以带来机会、合作和宝贵的见解。\n\n7.保持坚持：不要让挫折使你气馁。保持坚持，继续努力实现你的目标，即使面对挑战和失败。\n\n8.拥抱适应性：世界在不断变化，适应性至关重要。对能帮助你保持领先地位的新想法、技术和方法保持开放态度。\n\n9.积极心态：保持积极的态度，相信自己的能力。积极的心态不仅可以帮助你应对挑战，还可以吸引机会和与你分享热情的人。\n\n10.照顾自己：成功与你的整体幸福紧密相关。优先考虑你的身体、心理和情感健康。定期锻炼、健康饮食和充足的休息是必不可少的。\n\n11.寻求反馈：愿意接受导师、同行和同事的建设性批评和反馈。这可以帮助你找出需要改进的领域，并优化你的策略。\n\n12.管理风险：为了增长，经常需要冒一些计算过的风险。在做重大决策之前评估潜在的风险和回报，并准备好在事情不按计划进行时进行调整。\n\n13.保持坚持：实现成功通常需要耐心和毅力。面对挑战或进展缓慢时，不要放弃。继续前进。\n\n14.庆祝成就：花时间承认和庆祝你的成就，不管是大是小。认识到自己的进步可以激励你继续努力追求更多。\n\n15.创造价值：专注于为他人提供价值，无论是通过你的工作、产品还是服务。产生积极影响可以带来持久的成功和强大的声誉。\n\n请记住，成功是一个旅程，而不是目的地。重要的是要根据自己的标准来定义成功，并在成长和发展中不断重新评估你的目标。实现成功的方式因个人的愿望和情况而异。",
    "我没有预测未来的能力，因为我的知识只延伸到2021年9月。我无法提供有关此时间以后发生的事件、发展或变化的信息。如果您有关于可能的趋势或假设情景的问题，我当然可以帮助，但请记住，任何预测或见解都将是推测，而不是基于实际未来事件的。如果您想了解最近事件或当前状况的信息，我建议您查阅可靠的新闻来源或最新参考资料。",
    "追求幸福是一段复杂而个人的旅程，没有一种适合所有人的解决方案。然而，有几个通用的原则和实践方法可以有助于你的整体幸福感，增加你体验幸福的机会。以下是一些建议：\n\n1.培养积极的关系：与家人、朋友建立联系，建立有意义的关系，这对你的幸福感有显著影响。与支持和积极的人保持联系可以提供情感支持和归属感。\n\n2.实践感恩：定期花时间反思你感恩的事物。感恩之情可以将你的注意力从消极情绪转移开来，帮助你欣赏生活中的积极方面。\n\n3.参与喜欢的活动：参与能带给你快乐和满足感的爱好、兴趣和活动。参与你喜欢的事情可以提升你的情绪，带来成就感。\n\n4.关注身体健康：身体健康与心理和情感健康紧密相关。优先考虑定期锻炼、均衡饮食和充足的睡眠，以维持你的能量水平和整体健康。\n\n5.实践正念和冥想：正念技巧和冥想可以帮助你保持当下，减轻压力，改善整体幸福感。\n\n6.设定和追求有意义的目标：设定可实现的目标并朝着这些目标努力可以给你提供目的感和成就感。确保你的目标与你的价值观和兴趣相一致。\n\n7.帮助他人：参与善行和帮助他人可以提升你自己的幸福感。志愿工作或简单的善举可以带来满足感和连接感。\n\n8.管理压力：学习有效的压力管理技巧，如深呼吸、瑜伽或参与放松活动，可以帮助你应对挑战，并防止它们压垮你。\n\n9.减少负面影响：尽量减少负面新闻、有毒的关系和能量耗竭的环境的接触。尽可能让自己充满积极的能量。\n\n10.实践自我怜悯：善待自己，理解自己，尤其是在困难或挫折时。避免对自己过于苛责。\n\n11.找到平衡：在工作、关系、个人时间和休闲活动之间追求平衡。这可以防止过度劳累，增强整体幸福感。\n\n12.寻求专业帮助：如果你在持续感到不幸福，考虑寻求心理健康专业人士的指导。治疗或咨询可以为你提供有价值的工具，帮助你应对挑战，提高你的幸福感。\n\n请记住，幸福不是一个持续的状态；体验一系列情感是正常的。专注于培养韧性并养成有益的习惯，以促进你的整体幸福感。重要的是要耐心对待自己，并理解实现幸福是一个需要时间和努力的旅程。",
    "当然，选择阅读的书籍可以取决于你的兴趣，但这里有一个跨足多种类型和风格的书单，你可能会觉得有趣：\n\n1.小说：\n\n《杀死一只知更鸟》 哈珀·李\n《1984》 乔治·奥威尔\n《傲慢与偏见》 简·奥斯汀\n《了不起的盖茨比》 F. 斯科特·菲茨杰拉德\n《百年孤独》 加夫列尔·加西亚·马尔克斯\n2.科幻/奇幻：\n\n《沙丘》 弗兰克·赫伯特\n《指环王》 J.R.R. 托尔金\n《神经漫游者》 威廉·吉布森\n《时间的皱纹》 马德琳·朗格尔\n《饥饿游戏》 苏珊·柯林斯\n3.悬疑/惊悚：\n\n《失踪的女孩》 吉莉安·弗林\n《龙纹身的女孩》 斯蒂格·拉尔松\n《达·芬奇密码》 丹·布朗\n《无人生还》 阿加莎·克里斯蒂\n《沉默的病人》 亚历克斯·迈克赖迪斯\n4.历史小说：\n\n《所有我们看不见的光芒》 安东尼·多尔\n《偷书贼》 马库斯·祖萨克\n《狼厅》 希拉里·曼特尔\n《夜莺》 克里斯汀·汉娜\n《大教堂与市场》 肯·福莱特\n5.非虚构类：\n\n《人类简史：从动物到上帝》 尤瓦尔·诺亚·哈拉利\n《成为》 米歇尔·奥巴马\n《习惯的力量》 查尔斯·杜希格\n《思考，快与慢》 丹尼尔·卡尼曼\n《内向者的优势：在一个无法停止交谈的世界中的力量》 苏珊·凯恩\n6.自助/个人发展：\n\n《不给 F*ck 的微妙之道》 马克·曼森\n《原子习惯》 詹姆斯·克利尔\n《你真了不起》 珍·辛塞罗\n《高效能人士的七个习惯》 斯蒂芬·R·柯维\n《毅力：激情和毅力的力量》 安吉拉·达克沃斯\n7.经典文学：\n\n《白鲸》 赫尔曼·梅尔维尔\n《简·爱》 夏洛特·勃朗特\n《罪与罚》 费奥多尔·陀思妥耶夫斯基\n《麦田里的守望者》 J.D. 萨林格\n《呼啸山庄》 艾米莉·勃朗特\n请记住，每个人的口味都不同，所以不要犹豫去探索之前可能没有考虑过的类型。祝你阅读愉快！",
    "关于如何度过你的一生的问题是非常个人化且复杂的，回答起来可能不容易。重要的是要记住，没有一种适合所有人的答案，因为每个人的旅程都是独特的。然而，以下是一些步骤，可以帮助你找到自己的目标，做出有意义的决策：\n\n1.自我反思：花时间思考你的兴趣、价值观、优势和激情。考虑哪些活动让你快乐，哪些问题对你重要，你在哪些方面表现出色。\n\n2.设定目标：制定短期和长期目标。明确的目标可以为你提供方向和目的感。将更大的目标分解为可管理的小步骤。\n\n3.探索：尝试新事物，走出你的舒适区。探索不同的经历可以帮助你发现新的兴趣和才能。\n\n4.教育和技能发展：投资学习和技能发展。获得新知识和技能可以开启新的机会和职业道路。\n\n5.寻求指导：与导师、顾问和激励你的人交谈。他们可以根据自己的经验提供有价值的见解和观点。\n\n6.帮助他人：为他人的幸福作出贡献可以带来成就感和目的感。参与志愿工作或从事能够产生积极影响的角色可能会带来深刻的回报。\n\n7.适应能力：对变化持开放态度，愿意根据学习和成长做出调整。生活是充满活力的，灵活性可以引导你走向意想不到且充实的道路。\n\n8.平衡：追求一个平衡的生活，包括工作、人际关系、个人成长和休闲。在生活的不同领域找到和谐可以促进整体的幸福感。\n\n9.克服挑战：将挑战和挫折视为成长的机会。韧性和毅力是在发现你的人生道路时重要的品质。\n\n10.倾听自己：相信你的直觉和内心声音。通常情况下，你的直觉可以引导你做出与真实自我的决策。\n\n11.持续评估：定期评估你的进展并根据需要进行调整。随着时间的推移，你的兴趣和优先事项可能会发生变化，保持对这些变化的敏感性是很重要的。\n\n请记住，找到你人生的目标是一个持续的过程。如果你一时找不到所有答案，也没有关系。花时间，对自己保持耐心，专注于自我发现的旅程。如果你发现自己在挣扎或感到迷失，考虑寻求心理治疗师或咨询师的支持，他们可以帮助你应对这些挑战。",
    "提高生产力涉及采用有效的策略和习惯，以最大限度地利用你的时间和精力。以下是一些建议，可以帮助你提高生产力：\n\n1.设定明确目标：为你的任务和项目定义具体、可实现的目标。明确的目标会让你有方向感和目的感。\n\n2.优先处理任务：使用艾森豪威尔矩阵或番茄工作法等方法，根据紧急性和重要性对任务进行优先排序。\n\n3.创建待办事项清单：写下你的任务，并将它们组织成一个待办事项清单。这有助于你保持组织，并确保你不会忘记重要的任务。\n\n4.时间分块：为不同的任务分配特定的时间块。这有助于你专注于一项任务，防止多任务处理，从而降低整体生产力。\n\n5.消除干扰：识别和减少环境中的干扰，比如关闭通知、将手机静音，以及创造一个无杂乱的工作空间。\n\n6.明智使用技术：利用任务管理器、记事应用和日历应用等生产力应用和工具，保持组织并有效地管理你的时间。\n\n7.将任务分解为较小步骤：庞大的任务可能会让人感到压力。将它们分解为较小的可管理步骤，让它们显得不那么令人望而生畏，更容易实现。\n\n8.设定截止日期：为你的任务设定现实的截止日期，以创建紧迫感，帮助你保持在轨道上。\n\n9.实践时间管理：学会有效地管理你的时间，估计任务需要多长时间，并为它们分配适当的时间段。\n\n10.休息一下：定期休息可以让你的思维恢复活力，防止疲劳。考虑使用番茄工作法（工作25分钟，然后休息5分钟）等技巧。\n\n11.委派任务：如果可能，将一些其他人可以处理的任务委派出去，为更重要或高价值的任务腾出时间。\n\n12.学会说不：不要过度承诺。礼貌地拒绝与当前优先事项不符的任务或项目。\n\n13.专注于一件事情：多任务处理实际上可能会降低生产力。集中注意力于一项任务，以取得更好的结果。\n\n14.持续学习：投入时间学习新的技能，可以提高你在完成任务时的效率和效能。\n\n15.保持健康的生活方式：定期锻炼、适当的睡眠和均衡的饮食有助于提高能量水平和整体健康，从而提高生产力。\n\n16.回顾和反思：在一天或一周结束时，回顾你的成就，确定改进的领域。根据情况调整你的策略。\n\n17.优化你的工作空间：将工作空间安排得最高效。确保你手边有必要的工具和资源。\n\n18.使用积极强化：为完成任务或实现里程碑奖励自己。这有助于激励你保持生产力。\n\n19.实践正念：参与正念技巧，如冥想，可以提高注意力，减少压力，增强整体认知功能。\n\n20.实验和调整：每个人的生产力策略都是不同的。尝试不同的技术，并将它们适应到你自己的工作方式中。\n\n请记住，提高生产力需要时间和努力。从实施其中一些策略开始，逐渐将它们融入到你的日常生活中。随着时间的推移，你会找到最适合你的方法，并看到你的生产力得到提升。",
    "关于生命的意义的问题是一个深刻且哲学性的问题，几个世纪以来一直吸引着人类。没有一个适用于所有人的单一明确答案，因为它可以因个体的信仰、文化背景和个人观点而异。不同的哲学家、宗教和精神传统以及思想家对生命的意义提出了各种不同的解释。以下是一些观点：\n\n1.宗教和精神解释：许多宗教传统认为生命的意义与更高的目标或神圣计划有关。例如，在基督教中，生命的目的通常被视为是侍奉上帝并与上帝建立关系。在佛教中，重点可能是实现开悟和超越苦难。\n\n2.存在主义观点：存在主义哲学家如让-保罗·萨特和阿尔贝·加缪认为生命没有固有的意义，个体必须通过自己的选择和行动创造自己的意义。存在主义强调在定义生命目的时个人的个人自由和责任的重要性。\n\n3.哲学观点：来自不同思想流派的哲学家探讨了生命的意义问题。一些人认为意义可以在个人关系中找到，在追求知识中找到，在体验美和艺术中找到，或者在为他人和整个社会的幸福做出贡献中找到。\n\n4.科学和自然主义观点：从科学或自然主义的角度来看，生命的意义可能是进化和自然过程的复杂相互作用的结果。有些人可能会在探索和理解自然界和宇宙中找到意义。\n\n5.享乐主义观点：一些人认为生命的目的是追求快乐和幸福，强调追求愉快的体验，减少痛苦。\n\n最终，生命意义的问题是个人深入思考的问题，可能因人而异。许多人通过一系列因素找到意义，包括他们的人际关系、成就、个人价值观、对他人的贡献，以及追求个人成长和实现。在思考这个问题时，考虑到自己的信仰、价值观和经验是很重要的。",
    "保持健康涉及身体、心理和情感健康的综合。以下是一些值得考虑的关键原则：\n\n1.均衡饮食：摄取各种全食，包括水果、蔬菜、瘦肉、全谷物和健康脂肪。限制加工食品、含糖零食和过多的饱和脂肪和反式脂肪。\n\n2.定期锻炼：参与定期的体育活动。目标是进行有氧运动、力量训练和柔韧性锻炼的综合。找到喜欢的活动，以使锻炼可持续。\n\n3.充足睡眠：优先考虑睡眠，每晚目标是获得7-9小时的优质睡眠。睡眠对于整体健康、认知功能和情感健康至关重要。\n\n4.保持水分：全天饮用足够的水保持水分。水对于各种身体功能，包括消化和体温调节，都至关重要。\n\n5.应对压力：练习减压技巧，如冥想、深呼吸、瑜伽或正念。慢性压力可能会对身体和心理健康产生负面影响。\n\n6.社交联系：保持紧密的社交关系。与朋友和家人共度时间可以提升情绪并提供情感支持。\n\n7.正念和心理健康：关注自己的心理健康。实施自我关爱，需要时寻求帮助，并参与带来喜悦和放松的活动。\n\n8.避免有害物质：尽量减少或消除烟草、过度饮酒和娱乐药物的使用。这些物质可能对健康产生严重负面影响。\n\n9.定期体检：定期安排医学体检，以监测健康状况并及早发现潜在问题。遵循医疗保健提供者的建议进行筛查和接种疫苗。\n\n10.卫生习惯：保持良好的个人卫生，以防止病菌和感染的传播。\n\n11.持续学习：继续了解健康和健康。随着时间的推移，我们对健康的理解会不断更新，保持对最新研究和建议的了解。\n\n12.积极态度：培养积极的态度并实践感恩之心。积极的态度有助于改善心理和身体健康。\n\n请记住，每个人的健康之旅是独特的，适合一个人的方法可能不适合另一个人。重要的是找到适合自己的平衡，进行可持续的、逐渐的改变，而不是试图进行剧烈的改变。如果您有特定的健康问题或目标，请考虑咨询医疗专业人士或注册营养师以获取个性化的指导。"
]

for (x, y) in zip(A, B):
    while True:
        try:
            user_input = x
            answer_response = y
            response3 = openai.ChatCompletion.create(
                model='gpt-3.5-turbo',
                messages=[
                    {'role': 'user', 'content': x},
                    {'role': 'assistant', 'content': y},
                    {'role': 'user', 'content': "对于ChatGPT刚才的回答，答案中哪里可能是ChatGPT理解错误的地方，请标出ChatGPT生成的答案中至少5种且至少五处理解错误程度的词汇、并说出这对应用户提问“" + x + "”这句理解模糊的词汇并说明原因。答案格式为：【答案中原词汇】【用户提问中词汇】【1或2或3或4，代表理解错误程度，数值越大程度越深，要加左右括号】【原因】。\n例如：对于输入“怎样做prompt tuning更结构化的获得结果”，生成结果为“1. 要让prompt tuning更结构化，你可以通过优化prompt模板的设计来获得更好的结果。一种方法是使用预处理技术，例如利用词频统计将常见词组合并为一个token，以减少prompt长度和数量。另一种方法是利用语义相似性，在prompt中添加一些同义词和相关词以提高模型的理解和表达能力。 2. 如果你想要prompt tuning更加结构化，你可以考虑使用更有针对性的prompt，这可以通过对数据集进行分析和研究来实现。你可以观察数据集中的模式和趋势，这可以帮助你确定哪些prompt是最有效的，并指导你进行后续的调整和优化，帮助你获得更好的结果。 3. 一种改进prompt tuning结构的方法是使用GANs，通过对prompt的生成和修改达到更好的效果。GAN可以通过学习和生成高质量的prompt来表现出它们的优化能力。虽然这种方法需要更高水平的技术和资源，但它可以产生更好的结果和更高的效率，因为该方法会利用神经网络生成更优质的prompt。”，给出输出应该类似：“【使用GANs】 【prompt tuning更结构化】 【2】 \n【同义词和相关词】 【更有针对性的prompt】 【4】 \n【利用词频统计将常见词组合并为一个token】 【更结构化的获得结果】 【1】 ”"}
                ]
            )
            annotation_response = response3.choices[0].message['content']
            ann = annotation_response.split("\n")
            if '1' in annotation_response and ('2' in annotation_response) and ('3' in annotation_response) and ('4' in annotation_response):
                for single_response in ann:
                    keywords = re.findall(r'【(.*?)】', single_response)
                    if len(keywords) >= 3:
                        regex = re.compile(keywords[0])
                        level = eval(keywords[2])
                        color = colors[level-1]
                        # 逐个匹配字符串，并记录下标
                        matching_indices = [match.start() for match in regex.finditer(answer_response)]
                        # 遍历匹配到的下标，为其添加高亮样式
                        highlighted_text = ''
                        last_index = 0
                        print(keywords[0], matching_indices, color)
                        for index in matching_indices:
                            # 添加未匹配的文本内容
                            # highlighted_text += f'<span style="background-color: #C2ABC6;">{answer_response[last_index:index]}</span>'
                            highlighted_text += f'{answer_response[last_index:index]}'
                            # 添加高亮的文本内容
                            highlighted_text += f'<span style="background-color: {color};">{keywords[0]}</span>'
                            last_index = index + len(keywords[0])
                            
                        # 添加最后一个未匹配的文本内容
                        highlighted_text += f'{answer_response[last_index:]}'
                        # highlighted_text += f'<span style="background-color: #C2ABC6;">{answer_response[last_index:]}</span>'

                        # 将高亮后的文本以 HTML 形式输出
                        answer_response = highlighted_text
                        # 遍历匹配到的下标，为其添加高亮样式
                        for single_keyword in keywords[1].split("，"):
                            another_text = ''
                            regex = re.compile(single_keyword)
                            last_index = 0
                            another_matching = [match.start() for match in regex.finditer(user_input)]
                            for index in another_matching:
                                # 添加未匹配的文本内容
                                # another_text += f'<span style="background-color: #7F5A83;">{user_input[last_index:index]}</span>'
                                another_text += f'{user_input[last_index:index]}'
                                # 添加高亮的文本内容
                                another_text += f'<span style="background-color: {color};">{keywords[1]}</span>'
                                last_index = index + len(keywords[1])
                            
                            # 添加最后一个未匹配的文本内容
                            # another_text += f'<span style="background-color: #7F5A83;">{user_input[last_index:]}</span>'
                            another_text += f'{user_input[last_index:]}'
                            # 将高亮后的文本以 HTML 形式输出
                            user_input = another_text
                if user_input != x and answer_response != y and len(ann) > 6:
                    inputsss.append(user_input)
                    answersss.append(answer_response)
                    break
            else:
                time.sleep(3)
        except:
            traceback.print_exc()
            pass

with open("A_4.txt", "w", encoding='utf8') as f:
    for (x, y) in zip(inputsss, answersss):
        f.write("[INPUT] " + str(x) + "\n[ANSWER] " + str(y) + "\n")

ipdb.set_trace()

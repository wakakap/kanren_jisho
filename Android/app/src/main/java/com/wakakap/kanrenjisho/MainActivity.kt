package com.wakakap.kanrenjisho

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import com.wakakap.kanrenjisho.ui.composables.SearchScreen
import com.wakakap.kanrenjisho.ui.theme.KanrenJishoTheme // 确保主题名称正确
import com.wakakap.kanrenjisho.ui.viewmodel.DictionaryViewModel

class MainActivity : ComponentActivity() {

    // 使用 activity-ktx 库来获取 ViewModel 实例
    private val viewModel: DictionaryViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            // KanrenJishoTheme 是你在 ui.theme 包中定义的主题
            KanrenJishoTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    // 将 ViewModel 实例传递给主屏幕
                    SearchScreen(viewModel = viewModel)

                    // 注意：为了简单起见，我将收藏夹和调试视图集成到了 SearchScreen 中。
                    // 如果你想要一个真正的侧边栏，你需要使用 ModalNavigationDrawer。
                }
            }
        }
    }
}
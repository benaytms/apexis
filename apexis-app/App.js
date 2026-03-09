import { useState, useEffect } from 'react'
import AsyncStorage from '@react-native-async-storage/async-storage'
import {
  View,
  Text,
  Image,
  ScrollView,
  ActivityIndicator,
  StyleSheet,
  Dimensions,
  TouchableOpacity,
  Modal,
  StatusBar,
  RefreshControl,
} from 'react-native'

const API_BASE = "https://apod-production-9b08.up.railway.app"
const { width, height } = Dimensions.get('window')

export default function App() {
  const [imageData, setImageData] = useState(null)
  const [wordData, setWordData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [modalVisible, setModalVisible] = useState(false)
  const [refreshing, setRefreshing] = useState(false)

  const fetchToday = async () => {
    try {
      const [imgResponse, wordResponse] = await Promise.all([
        fetch(`${API_BASE}/image/today`),
        fetch(`${API_BASE}/word/today`),
      ])

      if (!imgResponse.ok) {
        throw new Error(`Image fetch failed: ${imgResponse.status}`)
      }

      if (!wordResponse.ok) {
        throw new Error(`Word fetch failed: ${wordResponse.status}`)
      }

      const img = await imgResponse.json()
      const word = await wordResponse.json()

      await AsyncStorage.setItem('cached_image', JSON.stringify(img))
      await AsyncStorage.setItem('cached_word', JSON.stringify(word))

      setImageData(img)
      setWordData(word)
      setError(null)

    } catch (e) {
      try {
        const cachedImg = await AsyncStorage.getItem('cached_image')
        const cachedWord = await AsyncStorage.getItem('cached_word')
        
        if (cachedImg && cachedWord) {
          setImageData(JSON.parse(cachedImg))
          setWordData(JSON.parse(cachedWord))
        } else {
          setError("No internet connection and no cached data available.")
        }
      } catch {
        setError(e.message || "Could not connect to server")
      }
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  const onRefresh = async () => {
    setRefreshing(true)
    await fetchToday()
  }

  useEffect(() => {
    fetchToday()
  }, [])

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#ffffff" />
        <Text style={styles.loadingText}>Loading...</Text>
      </View>
    )
  }

  if (error) {
    return (
      <View style={styles.centered}>
        <Text style={styles.errorText}>{error}</Text>
      </View>
    )
  }

  return (
    <View style={styles.wrapper}>
      <StatusBar barStyle="light-content" backgroundColor="#1a1a1a" />

      {/* fullscreen image modal */}
      <Modal
        visible={modalVisible}
        transparent={true}
        animationType="fade"
        onRequestClose={() => setModalVisible(false)}
      >
        <View style={styles.modalContainer}>
          <StatusBar hidden={true} />
          <Image
            source={{ uri: imageData?.url }}
            style={styles.modalImage}
            resizeMode="contain"
          />
          <TouchableOpacity
            style={styles.closeButton}
            onPress={() => setModalVisible(false)}
          >
            <Text style={styles.closeText}>✕</Text>
          </TouchableOpacity>
        </View>
      </Modal>

      <ScrollView
        contentContainerStyle={styles.container}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor="#ffffff"
            colors={["#ffffff"]}
          />
        }
      >
        {/* date */}
        <Text style={styles.date}>{imageData?.date}</Text>

        {/* tappable image or video notice */}
        {imageData?.media_type === 'image' ? (
          <TouchableOpacity onPress={() => setModalVisible(true)}>
            <Image
              source={{ uri: imageData?.url }}
              style={styles.image}
              resizeMode="cover"
            />
            <Text style={styles.tapHint}>tap to expand</Text>
          </TouchableOpacity>
        ) : (
          <View style={styles.videoContainer}>
            <Text style={styles.videoNotice}>🎬 Today's APOD is a video</Text>
            <Text style={styles.videoUrl}>{imageData?.url}</Text>
          </View>
        )}

        {/* image title */}
        <Text style={styles.imageTitle}>{imageData?.title}</Text>

        {/* copyright */}
        <Text style={styles.copyright}>{imageData?.copyright}</Text>

        {/* explanation */}
        <Text style={styles.explanation}>{imageData?.explanation}</Text>

        {/* divider */}
        <View style={styles.divider} />

        {/* word of the day */}
        <Text style={styles.wordLabel}>WORD OF THE DAY</Text>
        <Text style={styles.word}>{wordData?.word}</Text>
        <Text style={styles.definition}>{wordData?.definition}</Text>

        <View style={styles.bottomPadding} />
      </ScrollView>
    </View>
  )
}

const styles = StyleSheet.create({
  wrapper: {
    flex: 1,
    backgroundColor: '#1a1a1a',
  },
  container: {
    paddingHorizontal: 16,
    paddingVertical: 40,
  },
  centered: {
    flex: 1,
    backgroundColor: '#1a1a1a',
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    color: '#f7e479',
    marginTop: 12,
    fontSize: 14,
  },
  errorText: {
    color: '#ff4444',
    fontSize: 15,
    textAlign: 'center',
    paddingHorizontal: 40,
  },
  date: {
    color: '#ffd96f',
    fontSize: 12,
    marginBottom: 14,
  },
  image: {
    width: width - 32,
    height: (width - 32) * 0.65,
    borderRadius: 4,
    marginBottom: 6,
  },
  tapHint: {
    color: '#666666',
    fontSize: 11,
    marginBottom: 14,
    textAlign: 'right',
  },
  imageTitle: {
    color: '#ffffff',
    fontSize: 20,
    fontWeight: '600',
    marginBottom: 10,
    lineHeight: 28,
  },
  copyright: {
    color: '#ffd96f',
    fontSize: 12,
    marginBottom: 10,
  },
  explanation: {
    color: '#bbbbbb',
    fontSize: 14,
    lineHeight: 22,
    marginBottom: 28,
  },
  divider: {
    height: 1,
    backgroundColor: '#333333',
    marginBottom: 28,
  },
  wordLabel: {
    color: '#ffd96f',
    fontSize: 11,
    marginBottom: 8,
  },
  word: {
    color: '#ffffff',
    fontSize: 28,
    fontWeight: '600',
    marginBottom: 10,
  },
  definition: {
    color: '#bbbbbb',
    fontSize: 14,
    lineHeight: 22,
  },
  bottomPadding: {
    height: 60,
  },
  modalContainer: {
    flex: 1,
    backgroundColor: '#000000',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalImage: {
    width: width,
    height: height,
  },
  closeButton: {
    position: 'absolute',
    top: 50,
    right: 20,
    backgroundColor: 'rgba(0,0,0,0.6)',
    borderRadius: 4,
    width: 36,
    height: 36,
    justifyContent: 'center',
    alignItems: 'center',
  },
  closeText: {
    color: '#ffffff',
    fontSize: 15,
  },
  videoContainer: {
    width: width - 32,
    height: (width - 32) * 0.65,
    borderRadius: 4,
    backgroundColor: '#2a2a2a',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 14,
  },
  videoNotice: {
    color: '#f7e479',
    fontSize: 15,
    marginBottom: 8,
  },
  videoUrl: {
    color: '#666666',
    fontSize: 11,
    textAlign: 'center',
    paddingHorizontal: 20,
  },
})